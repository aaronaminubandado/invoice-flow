from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import invoices, dashboard, webhooks, clients
from app.api.public import router as public_router
from app.api.metrics import router as metrics_router
from app.api.settings import router as settings_router
from app.api.middleware import (
    GlobalExceptionHandler,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
)
from app.core.config import settings
from app.services.scheduler import invoice_scheduler
from app.core.database import engine, AsyncSessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = invoice_scheduler.init_scheduler()
    scheduler.start()
    yield
    invoice_scheduler.shutdown()


app = FastAPI(
    title="InvoiceFlow",
    version="1.0.0",
    description="An API for automating invoice generation and management.",
    lifespan=lifespan,
)

# CORS configuration: in development we allow local Vite URLs,
# in production we read the browser origin from FRONTEND_ORIGIN.
cors_origins: list[str] = [
    "http://localhost:5173",
    "http://localhost:5174",
]

if settings.ENV.lower() != "development" and settings.FRONTEND_ORIGIN:
    cors_origins.append(settings.FRONTEND_ORIGIN.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GlobalExceptionHandler)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

app.include_router(invoices.router)
app.include_router(public_router)
app.include_router(dashboard.router)
app.include_router(webhooks.router)
app.include_router(clients.router)
app.include_router(metrics_router)
app.include_router(settings_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
