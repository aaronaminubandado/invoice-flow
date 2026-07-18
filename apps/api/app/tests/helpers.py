import secrets
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_test_client(
    db_session: AsyncSession,
    user_id: UUID,
    *,
    client_id: UUID | None = None,
    name: str = "Test Client",
    email: str = "test@example.com",
) -> UUID:
    client_id = client_id or uuid4()
    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, :name, :email)
            """
        ),
        {
            "client_id": client_id,
            "user_id": user_id,
            "name": name,
            "email": email,
        },
    )
    return client_id


async def insert_test_invoice(
    db_session: AsyncSession,
    user_id: UUID,
    client_id: UUID,
    *,
    invoice_id: UUID | None = None,
    amount: float = 1000.00,
    status: str = "sent",
    due_date_expr: str = "CURRENT_DATE",
    invoice_number: str | None = None,
    share_token: str | None = None,
    email_status: str | None = None,
    last_email_error: str | None = None,
    created_at_expr: str | None = None,
) -> UUID:
    invoice_id = invoice_id or uuid4()
    share_token = share_token or secrets.token_urlsafe(24)

    columns = [
        "id",
        "user_id",
        "client_id",
        "amount",
        "due_date",
        "status",
        "share_token",
    ]
    values = [
        ":invoice_id",
        ":user_id",
        ":client_id",
        ":amount",
        due_date_expr,
        ":status",
        ":share_token",
    ]
    params: dict = {
        "invoice_id": invoice_id,
        "user_id": user_id,
        "client_id": client_id,
        "amount": amount,
        "status": status,
        "share_token": share_token,
    }

    if invoice_number is not None:
        columns.append("invoice_number")
        values.append(":invoice_number")
        params["invoice_number"] = invoice_number

    if email_status is not None:
        columns.append("email_status")
        values.append(":email_status")
        params["email_status"] = email_status

    if last_email_error is not None:
        columns.append("last_email_error")
        values.append(":last_email_error")
        params["last_email_error"] = last_email_error

    if created_at_expr is not None:
        columns.append("created_at")
        values.append(created_at_expr)

    sql = f"""
        INSERT INTO invoices ({", ".join(columns)})
        VALUES ({", ".join(values)})
    """
    await db_session.execute(text(sql), params)
    return invoice_id
