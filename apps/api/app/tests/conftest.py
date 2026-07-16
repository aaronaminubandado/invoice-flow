import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.main import app
from app.core.config import settings
from uuid import uuid4


TEST_DATABASE_URL = settings.DATABASE_URL

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    user_id = uuid4()
    return user_id


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, test_user: uuid4):
    from app.deps import get_current_user
    from app.core.database import get_db

    async def override_get_current_user():
        return test_user

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await db_session.rollback()


@pytest.fixture
def user_id(test_user: uuid4):
    return test_user
