from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.deps import get_current_user
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientListOut
from app.services.export import generate_csv, generate_xlsx, generate_pdf_table

router = APIRouter(prefix="/clients", tags=["Clients"])

CLIENT_EXPORT_HEADERS = ["Name", "Email", "Phone", "Address", "Created At"]


@router.get("/export")
async def export_clients(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    format: Optional[str] = Query("csv", regex="^(csv|xlsx|pdf)$"),
):
    """Export all clients as CSV, Excel, or PDF."""
    result = await db.execute(
        text("""
            SELECT id, name, email, phone, address, created_at
            FROM clients
            WHERE user_id = :uid
            ORDER BY created_at DESC
        """),
        {"uid": user_id},
    )

    rows_raw = result.fetchall()

    if not rows_raw:
        if format == "csv":
            return Response(
                content="No clients to export",
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=clients.csv"},
            )
        raise HTTPException(404, "No clients to export")

    rows = []
    for row in rows_raw:
        data = dict(row._mapping)
        rows.append([
            data.get("name", ""),
            data.get("email", ""),
            data.get("phone", "") or "",
            data.get("address", "") or "",
            str(data.get("created_at", "")),
        ])

    if format == "xlsx":
        content = generate_xlsx(CLIENT_EXPORT_HEADERS, rows, sheet_name="Clients")
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=clients.xlsx"},
        )

    if format == "pdf":
        content = generate_pdf_table(CLIENT_EXPORT_HEADERS, rows, title="Clients Export")
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=clients.pdf"},
        )

    content = generate_csv(CLIENT_EXPORT_HEADERS, rows)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clients.csv"},
    )


@router.get("/search", response_model=list[ClientResponse])
async def search_clients(
    q: str,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search clients by name or email."""
    result = await db.execute(
        text("""
            SELECT id, name, email, created_at
            FROM clients
            WHERE user_id = :uid
              AND (name ILIKE :query OR email ILIKE :query)
            ORDER BY created_at DESC
            LIMIT 20
        """),
        {"uid": user_id, "query": f"%{q}%"},
    )

    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]


@router.post("", response_model=ClientResponse)
async def create_client(
    payload: ClientCreate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client owned by the authenticated user."""
    result = await db.execute(
        text("""
            INSERT INTO clients (user_id, name, email, phone, address)
            VALUES (:uid, :name, :email, :phone, :address)
            RETURNING id, name, email, phone, address, created_at
        """),
        {
            "uid": user_id,
            "name": payload.name,
            "email": payload.email,
            "phone": payload.phone,
            "address": payload.address,
        },
    )

    row = result.first()
    if not row:
        raise HTTPException(500, "Failed to create client")

    await db.commit()
    return dict(row._mapping)


@router.get("", response_model=ClientListOut)
async def list_clients(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List clients belonging to the authenticated user with pagination."""
    count_result = await db.execute(
        text("SELECT COUNT(*) AS total FROM clients WHERE user_id = :uid"),
        {"uid": user_id},
    )
    total = int(count_result.scalar() or 0)

    result = await db.execute(
        text("""
            SELECT id, name, email, phone, address, created_at
            FROM clients
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {"uid": user_id, "limit": limit, "offset": offset},
    )
    items = [dict(row._mapping) for row in result.fetchall()]
    return {"items": items, "total": total}


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a specific client owned by the authenticated user."""
    result = await db.execute(
        text("""
            SELECT id, name, email, phone, address, created_at
            FROM clients
            WHERE id = :cid AND user_id = :uid
        """),
        {"cid": client_id, "uid": user_id},
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Client not found")
    return dict(row._mapping)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    payload: ClientUpdate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a client owned by the authenticated user."""
    result = await db.execute(
        text("""
            UPDATE clients
            SET name = COALESCE(:name, name),
                email = COALESCE(:email, email),
                phone = COALESCE(:phone, phone),
                address = COALESCE(:address, address)
            WHERE id = :cid AND user_id = :uid
            RETURNING id, name, email, phone, address, created_at
        """),
        {
            "name": payload.name,
            "email": payload.email,
            "phone": payload.phone,
            "address": payload.address,
            "cid": client_id,
            "uid": user_id,
        },
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Client not found")

    await db.commit()
    return dict(row._mapping)


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a client if it has no associated invoices."""
    result = await db.execute(
        text("SELECT id FROM clients WHERE id = :cid AND user_id = :uid"),
        {"cid": client_id, "uid": user_id},
    )
    client = result.first()

    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    result = await db.execute(
        text("SELECT 1 FROM invoices WHERE client_id = :cid LIMIT 1"),
        {"cid": client_id},
    )

    if result.first() is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete client with associated invoices",
        )

    await db.execute(
        text("DELETE FROM clients WHERE id = :cid AND user_id = :uid"),
        {"cid": client_id, "uid": user_id},
    )

    await db.commit()
    return
