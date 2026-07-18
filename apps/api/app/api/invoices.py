import logging
import secrets
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.deps import get_current_user
from app.core.database import get_db
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceOut,
    InvoiceListOut,
    PaymentCreate,
    PaymentOut,
    InvoiceWithPaymentsOut,
)
from app.services.email import EmailService
from app.services.invoice_state import (
    validate_transition,
    is_terminal_status,
    InvoiceStatus,
)
from app.services.pdf import PDFService
from app.services.api_errors import invoice_create_error_message
from app.services.invoice_pdf import build_invoice_pdf_bytes
from app.services.invoice_number import InvoiceNumberService
from app.services.business_settings import get_business_settings
from app.services.export import generate_csv, generate_xlsx, generate_pdf_table
from app.services.invoice_items import (
    compute_invoice_total,
    insert_invoice_items,
    replace_invoice_items,
    fetch_invoice_items,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices", tags=["Invoices"])

INVOICE_SELECT = """
    SELECT
        i.id, i.user_id, i.client_id, i.amount, i.description,
        i.due_date, i.status, i.created_at, i.invoice_number,
        i.share_token, c.name AS client_name, c.email AS client_email,
        COALESCE(p.paid, 0)::NUMERIC(12,2) AS paid_amount,
        GREATEST(i.amount - COALESCE(p.paid, 0), 0)::NUMERIC(12,2) AS balance_due
    FROM invoices i
    JOIN clients c ON i.client_id = c.id
    LEFT JOIN (
        SELECT invoice_id, SUM(amount) AS paid
        FROM payments
        GROUP BY invoice_id
    ) p ON p.invoice_id = i.id
"""


async def _build_invoice_out(db: AsyncSession, row) -> dict:
    data = dict(row._mapping)
    data["items"] = await fetch_invoice_items(db, data["id"])
    return data


EXPORT_HEADERS = [
    "Invoice Number",
    "Client Name",
    "Client Email",
    "Amount",
    "Description",
    "Due Date",
    "Status",
    "Created At",
]


@router.get("/export")
async def export_invoices(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    format: Optional[str] = Query("csv", pattern="^(csv|xlsx|pdf)$"),
):
    """Export all invoices as CSV, Excel, or PDF."""
    result = await db.execute(
        text("""
            SELECT
                i.id,
                i.invoice_number,
                i.amount,
                i.description,
                i.due_date,
                i.status,
                i.created_at,
                c.name as client_name,
                c.email as client_email
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            WHERE i.user_id = :uid
            ORDER BY i.created_at DESC
        """),
        {"uid": user_id},
    )

    rows_raw = result.fetchall()

    if not rows_raw:
        if format == "csv":
            return Response(
                content="No invoices to export",
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=invoices.csv"},
            )
        raise HTTPException(404, "No invoices to export")

    rows = []
    for row in rows_raw:
        data = dict(row._mapping)
        rows.append([
            data.get("invoice_number", ""),
            data.get("client_name", ""),
            data.get("client_email", ""),
            str(data.get("amount", "")),
            data.get("description", ""),
            str(data.get("due_date", "")),
            data.get("status", ""),
            str(data.get("created_at", "")),
        ])

    if format == "xlsx":
        content = generate_xlsx(EXPORT_HEADERS, rows, sheet_name="Invoices")
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=invoices.xlsx"},
        )

    if format == "pdf":
        content = generate_pdf_table(EXPORT_HEADERS, rows, title="Invoices Export")
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=invoices.pdf"},
        )

    content = generate_csv(EXPORT_HEADERS, rows)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices.csv"},
    )


@router.post("", response_model=InvoiceOut)
async def create_invoice(
    payload: InvoiceCreate,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new invoice for a client owned by the authenticated user."""
    try:
        client_check = await db.execute(
            text("SELECT id FROM clients WHERE id = :cid AND user_id = :uid"),
            {"cid": payload.client_id, "uid": user_id},
        )

        if client_check.first() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        invoice_number = await InvoiceNumberService.generate_invoice_number(
            db, user_id
        )

        share_token = secrets.token_urlsafe(24)
        if payload.items:
            amount = compute_invoice_total(payload.items)
        else:
            amount = payload.amount

        initial_status = "sent" if payload.send_now else "draft"

        result = await db.execute(
            text("""
                INSERT INTO invoices (
                    user_id, client_id, amount, description,
                    due_date, status, invoice_number,
                    reminder_count, email_status, share_token
                )
                VALUES (
                    :uid, :cid, :amount, :description,
                    :due_date, :status, :invoice_number,
                    0, 'pending', :share_token
                )
                RETURNING id, user_id, client_id, amount, description, due_date,
                          status, created_at, invoice_number, share_token
            """),
            {
                "uid": user_id,
                "cid": payload.client_id,
                "amount": amount,
                "description": payload.description,
                "due_date": payload.due_date,
                "invoice_number": invoice_number,
                "share_token": share_token,
                "status": initial_status,
            },
        )

        row = result.first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create invoice",
            )

        invoice_data = dict(row._mapping)

        if payload.items:
            await insert_invoice_items(db, invoice_data["id"], payload.items)

        await db.commit()

        client_result = await db.execute(
            text("SELECT email, name FROM clients WHERE id = :client_id"),
            {"client_id": payload.client_id},
        )
        client_row = client_result.first()
        client_email = client_row.email if client_row else None
        client_name = client_row.name if client_row else "Customer"

        items_payload = []
        if payload.items:
            for item in payload.items:
                from app.services.invoice_items import compute_line_total

                items_payload.append(
                    {
                        "description": item.description,
                        "quantity": str(item.quantity),
                        "unit_price": str(item.unit_price),
                        "line_total": str(
                            compute_line_total(item.quantity, item.unit_price)
                        ),
                    }
                )

        if payload.send_now and client_email:
            background_tasks.add_task(
                EmailService.send_invoice_email_with_tracking,
                invoice_id=str(invoice_data["id"]),
                to=client_email,
                invoice_data={
                    "amount": str(amount),
                    "description": payload.description or "",
                    "due_date": str(payload.due_date),
                    "invoice_number": invoice_number,
                    "share_token": share_token,
                    "client_name": client_name,
                    "items": items_payload,
                },
            )

        full = await db.execute(
            text(f"{INVOICE_SELECT} WHERE i.id = :id"),
            {"id": invoice_data["id"]},
        )
        return await _build_invoice_out(db, full.first())

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to create invoice")
        status_code, detail = invoice_create_error_message(e)
        raise HTTPException(status_code=status_code, detail=detail)


@router.get("", response_model=InvoiceListOut)
async def list_invoices(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
):
    """List invoices belonging to the authenticated user with pagination."""
    where_parts = ["i.user_id = :uid"]
    params: dict = {"uid": user_id, "limit": limit, "offset": offset}

    if status and status != "all":
        where_parts.append("i.status = :status")
        params["status"] = status

    where_clause = " AND ".join(where_parts)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) AS total FROM invoices i WHERE {where_clause}"),
        params,
    )
    total = int(count_result.scalar() or 0)

    result = await db.execute(
        text(f"""
            {INVOICE_SELECT}
            WHERE {where_clause}
            ORDER BY i.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    rows = []
    for row in result.fetchall():
        data = dict(row._mapping)
        data["items"] = []
        rows.append(data)
    return {"items": rows, "total": total}


@router.get("/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a specific invoice belonging to the authenticated user."""
    result = await db.execute(
        text(f"""
            {INVOICE_SELECT}
            WHERE i.id = :invoice_id AND i.user_id = :uid
        """),
        {"invoice_id": invoice_id, "uid": user_id},
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Invoice not found")
    return await _build_invoice_out(db, row)


@router.get("/{invoice_id}/payments", response_model=list[PaymentOut])
async def list_invoice_payments(
    invoice_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List payments recorded for an invoice."""
    check = await db.execute(
        text("SELECT id FROM invoices WHERE id = :invoice_id AND user_id = :uid"),
        {"invoice_id": invoice_id, "uid": user_id},
    )
    if check.first() is None:
        raise HTTPException(404, "Invoice not found")

    result = await db.execute(
        text("""
            SELECT id, invoice_id, amount, payment_method, payment_date, reference, created_at
            FROM payments
            WHERE invoice_id = :invoice_id
            ORDER BY created_at ASC
        """),
        {"invoice_id": invoice_id},
    )
    return [dict(row._mapping) for row in result.fetchall()]


@router.get("/{invoice_id}/email-status")
async def get_email_status(
    invoice_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the email delivery status for an invoice"""
    result = await db.execute(
        text("""
            SELECT id, email_status, last_email_error, last_email_sent_at, email_resend_id
            FROM invoices
            WHERE id = :invoice_id AND user_id = :uid
        """),
        {"invoice_id": invoice_id, "uid": user_id},
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Invoice not found")
    return dict(row._mapping)


@router.put("/{invoice_id}", response_model=InvoiceOut)
async def update_invoice(
    invoice_id: UUID,
    payload: InvoiceCreate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a specific invoice belonging to the authenticated user."""
    existing = await db.execute(
        text("SELECT status FROM invoices WHERE id = :invoice_id AND user_id = :uid"),
        {"invoice_id": invoice_id, "uid": user_id},
    )
    existing_row = existing.first()
    if not existing_row:
        raise HTTPException(404, "Invoice not found")

    current_status = dict(existing_row._mapping)["status"]
    if current_status not in ("draft", "sent"):
        payments_check = await db.execute(
            text("SELECT 1 FROM payments WHERE invoice_id = :invoice_id LIMIT 1"),
            {"invoice_id": invoice_id},
        )
        if payments_check.first() is not None or current_status in (
            "paid",
            "partial",
            "cancelled",
            "void",
            "overdue",
        ):
            raise HTTPException(
                409,
                f"Cannot edit invoice with status '{current_status}'",
            )

    if payload.items:
        amount = compute_invoice_total(payload.items)
    else:
        amount = payload.amount

    result = await db.execute(
        text("""
            UPDATE invoices
            SET client_id = :client_id,
                amount = :amount,
                description = :description,
                due_date = :due_date
            WHERE id = :invoice_id AND user_id = :uid
            RETURNING id
        """),
        {
            "invoice_id": invoice_id,
            "uid": user_id,
            "client_id": payload.client_id,
            "amount": amount,
            "description": payload.description,
            "due_date": payload.due_date,
        },
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Invoice not found")

    if payload.items:
        await replace_invoice_items(db, invoice_id, payload.items)

    await db.commit()

    full = await db.execute(
        text(f"{INVOICE_SELECT} WHERE i.id = :id"),
        {"id": invoice_id},
    )
    return await _build_invoice_out(db, full.first())


@router.post("/{invoice_id}/resend")
async def resend_invoice(
    invoice_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT i.id, i.invoice_number, i.amount, i.description, i.due_date,
                   i.share_token, c.email, c.name
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            WHERE i.id = :invoice_id AND i.user_id = :uid
        """),
        {"invoice_id": invoice_id, "uid": user_id},
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Invoice not found")

    invoice_data = dict(row._mapping)
    items = await fetch_invoice_items(db, invoice_id)
    items_payload = [
        {
            "description": i.description,
            "quantity": str(i.quantity),
            "unit_price": str(i.unit_price),
            "line_total": str(i.line_total),
        }
        for i in items
    ]

    background_tasks.add_task(
        EmailService.send_invoice_email_with_tracking,
        invoice_id=str(invoice_id),
        to=invoice_data["email"],
        invoice_data={
            "amount": str(invoice_data["amount"]),
            "description": invoice_data["description"] or "",
            "due_date": str(invoice_data["due_date"]),
            "invoice_number": invoice_data["invoice_number"],
            "share_token": invoice_data.get("share_token"),
            "client_name": invoice_data.get("name", "Customer"),
            "items": items_payload,
        },
    )

    return {"message": "Invoice email resent"}


@router.post("/{invoice_id}/send", response_model=InvoiceOut)
async def send_invoice(
    invoice_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transition a draft invoice to sent and email the client."""
    result = await db.execute(
        text("""
            SELECT i.id, i.status, i.invoice_number, i.amount, i.description,
                   i.due_date, i.share_token, c.email, c.name
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            WHERE i.id = :invoice_id AND i.user_id = :uid
            FOR UPDATE
        """),
        {"invoice_id": invoice_id, "uid": user_id},
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Invoice not found")

    invoice_data = dict(row._mapping)
    current_status = invoice_data["status"]

    valid, error_msg = validate_transition(current_status, InvoiceStatus.SENT.value)
    if not valid:
        raise HTTPException(400, error_msg)

    await db.execute(
        text("""
            UPDATE invoices
            SET status = 'sent', last_email_sent_at = NOW()
            WHERE id = :invoice_id
        """),
        {"invoice_id": invoice_id},
    )

    await db.execute(
        text("""
            INSERT INTO invoice_status_history (invoice_id, from_status, to_status, changed_by, reason)
            VALUES (:invoice_id, :from_status, 'sent', :changed_by, :reason)
        """),
        {
            "invoice_id": invoice_id,
            "from_status": current_status,
            "changed_by": user_id,
            "reason": "Invoice sent by user",
        },
    )

    await db.commit()

    items = await fetch_invoice_items(db, invoice_id)
    items_payload = [
        {
            "description": i.description,
            "quantity": str(i.quantity),
            "unit_price": str(i.unit_price),
            "line_total": str(i.line_total),
        }
        for i in items
    ]

    client_email = invoice_data.get("email")
    if client_email:
        background_tasks.add_task(
            EmailService.send_invoice_email_with_tracking,
            invoice_id=str(invoice_id),
            to=client_email,
            invoice_data={
                "amount": str(invoice_data["amount"]),
                "description": invoice_data["description"] or "",
                "due_date": str(invoice_data["due_date"]),
                "invoice_number": invoice_data["invoice_number"],
                "share_token": invoice_data.get("share_token"),
                "client_name": invoice_data.get("name", "Customer"),
                "items": items_payload,
            },
        )

    full = await db.execute(
        text(f"{INVOICE_SELECT} WHERE i.id = :id"),
        {"id": invoice_id},
    )
    return await _build_invoice_out(db, full.first())


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific invoice belonging to the authenticated user."""
    check = await db.execute(
        text("SELECT status FROM invoices WHERE id = :invoice_id AND user_id = :uid"),
        {"invoice_id": invoice_id, "uid": user_id},
    )
    row = check.first()
    if not row:
        raise HTTPException(404, "Invoice not found")

    current_status = dict(row._mapping)["status"]
    payments = await db.execute(
        text("SELECT 1 FROM payments WHERE invoice_id = :invoice_id LIMIT 1"),
        {"invoice_id": invoice_id},
    )
    if payments.first() is not None:
        raise HTTPException(409, "Cannot delete invoice with recorded payments")

    if current_status not in ("draft", "cancelled"):
        raise HTTPException(
            409,
            f"Cannot delete invoice with status '{current_status}'. Cancel it first.",
        )

    result = await db.execute(
        text("DELETE FROM invoices WHERE id = :invoice_id AND user_id = :uid RETURNING id"),
        {"invoice_id": invoice_id, "uid": user_id},
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Invoice not found")

    await db.commit()
    return {"message": "Invoice deleted"}


@router.post("/{invoice_id}/cancel")
async def cancel_invoice(
    invoice_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT id, status
            FROM invoices
            WHERE id = :invoice_id AND user_id = :uid
            FOR UPDATE
        """),
        {"invoice_id": invoice_id, "uid": user_id},
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Invoice not found")

    current_status = dict(row._mapping)["status"]

    valid, error_msg = validate_transition(current_status, "cancelled")
    if not valid:
        raise HTTPException(400, error_msg)

    await db.execute(
        text("UPDATE invoices SET status = 'cancelled' WHERE id = :invoice_id"),
        {"invoice_id": invoice_id},
    )

    await db.execute(
        text("""
            INSERT INTO invoice_status_history (invoice_id, from_status, to_status, changed_by, reason)
            VALUES (:invoice_id, :from_status, 'cancelled', :changed_by, :reason)
        """),
        {
            "invoice_id": invoice_id,
            "from_status": current_status,
            "changed_by": user_id,
            "reason": "Cancelled by user",
        },
    )

    await db.commit()

    return {
        "message": "Invoice cancelled successfully",
        "invoice_id": invoice_id,
        "status": "cancelled",
    }


@router.post("/{invoice_id}/payments", response_model=InvoiceWithPaymentsOut)
async def create_payment(
    invoice_id: UUID,
    payload: PaymentCreate,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a payment for an invoice. Supports partial payments."""
    payment_date = payload.payment_date or date.today()

    result = await db.execute(
        text("""
            SELECT id, amount, status, due_date
            FROM invoices
            WHERE id = :invoice_id AND user_id = :uid
            FOR UPDATE
        """),
        {"invoice_id": invoice_id, "uid": user_id},
    )

    invoice_row = result.first()
    if not invoice_row:
        raise HTTPException(404, "Invoice not found")

    invoice_row = dict(invoice_row._mapping)
    invoice_amount = Decimal(str(invoice_row["amount"]))
    current_status = invoice_row["status"]

    if current_status == InvoiceStatus.PAID.value:
        raise HTTPException(400, "Invoice is already paid")

    if is_terminal_status(current_status):
        raise HTTPException(
            400, f"Cannot add payment to invoice with status '{current_status}'"
        )

    valid, error_msg = validate_transition(current_status, InvoiceStatus.PAID.value)
    if not valid and current_status != InvoiceStatus.PARTIAL.value:
        valid_paid, _ = validate_transition(
            current_status, InvoiceStatus.PARTIAL.value
        )
        if not valid_paid:
            raise HTTPException(400, error_msg)

    total_paid_result = await db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) as total_paid
            FROM payments
            WHERE invoice_id = :invoice_id
        """),
        {"invoice_id": invoice_id},
    )
    total_paid_row = total_paid_result.first()
    total_paid = (
        Decimal(str(dict(total_paid_row._mapping)["total_paid"]))
        if total_paid_row
        else Decimal("0")
    )

    remaining = invoice_amount - total_paid

    if payload.amount > remaining:
        raise HTTPException(
            400,
            f"Payment amount {payload.amount} exceeds remaining {remaining}. "
            f"Invoice amount: {invoice_amount}, Already paid: {total_paid}",
        )

    payment_result = await db.execute(
        text("""
            INSERT INTO payments (
                invoice_id, amount, payment_method,
                payment_date, reference, notes, created_by
            )
            VALUES (
                :invoice_id, :amount, :payment_method,
                :payment_date, :reference, :notes, :created_by
            )
            RETURNING id, invoice_id, amount, payment_method, payment_date, reference, notes, created_at
        """),
        {
            "invoice_id": invoice_id,
            "amount": payload.amount,
            "payment_method": payload.payment_method,
            "payment_date": payment_date,
            "reference": payload.reference,
            "notes": payload.notes,
            "created_by": user_id,
        },
    )

    new_total_paid = total_paid + payload.amount

    new_status = "paid" if new_total_paid >= invoice_amount else "partial"

    await db.execute(
        text("UPDATE invoices SET status = :new_status WHERE id = :invoice_id"),
        {"new_status": new_status, "invoice_id": invoice_id},
    )

    await db.execute(
        text("""
            INSERT INTO invoice_status_history (invoice_id, from_status, to_status, changed_by, reason)
            VALUES (:invoice_id, :from_status, :to_status, :changed_by, :reason)
        """),
        {
            "invoice_id": invoice_id,
            "from_status": current_status,
            "to_status": new_status,
            "changed_by": user_id,
            "reason": f"Payment recorded: {payload.amount}",
        },
    )

    await db.commit()

    payment_row = payment_result.first()

    if new_total_paid >= invoice_amount:
        try:
            receipt_invoice_result = await db.execute(
                text("""
                    SELECT i.id, i.invoice_number, i.amount, i.share_token,
                           c.email, c.name
                    FROM invoices i
                    JOIN clients c ON i.client_id = c.id
                    WHERE i.id = :invoice_id
                """),
                {"invoice_id": invoice_id},
            )
            receipt_invoice_data = dict(receipt_invoice_result.first()._mapping)

            background_tasks.add_task(
                EmailService.send_receipt_email_with_tracking,
                invoice_id=str(invoice_id),
                to=receipt_invoice_data["email"],
                receipt_data={
                    "amount": str(invoice_amount),
                    "invoice_number": receipt_invoice_data["invoice_number"],
                    "payment_date": str(payment_date),
                    "paid_amount": str(new_total_paid),
                    "payment_method": payload.payment_method,
                    "share_token": receipt_invoice_data.get("share_token"),
                    "client_name": receipt_invoice_data.get("name", "Customer"),
                },
            )
        except Exception as e:
            logger.error(f"Failed to queue receipt email: {e}")

    invoice_result = await db.execute(
        text("SELECT id, amount, status FROM invoices WHERE id = :invoice_id"),
        {"invoice_id": invoice_id},
    )
    invoice_data = dict(invoice_result.first()._mapping)

    payments_result = await db.execute(
        text("""
            SELECT id, invoice_id, amount, payment_method, payment_date, reference, created_at
            FROM payments
            WHERE invoice_id = :invoice_id
            ORDER BY created_at ASC
        """),
        {"invoice_id": invoice_id},
    )

    return {
        "id": invoice_data["id"],
        "amount": invoice_data["amount"],
        "status": invoice_data["status"],
        "paid_amount": new_total_paid,
        "payments": [dict(row._mapping) for row in payments_result.fetchall()],
    }


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceOut)
async def mark_invoice_paid(
    invoice_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an invoice as fully paid. Creates a payment for the outstanding amount if needed."""
    result = await db.execute(
        text("""
            SELECT id, amount, status
            FROM invoices
            WHERE id = :invoice_id AND user_id = :uid
            FOR UPDATE
        """),
        {"invoice_id": invoice_id, "uid": user_id},
    )

    invoice_row = result.first()
    if not invoice_row:
        raise HTTPException(404, "Invoice not found")

    invoice_row = dict(invoice_row._mapping)
    invoice_amount = Decimal(str(invoice_row["amount"]))
    current_status = invoice_row["status"]

    if current_status in ("paid", "cancelled", "void"):
        raise HTTPException(400, f"Invoice already has status '{current_status}'")

    total_paid_result = await db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) as total_paid
            FROM payments
            WHERE invoice_id = :invoice_id
        """),
        {"invoice_id": invoice_id},
    )
    total_paid_row = total_paid_result.first()
    total_paid = (
        Decimal(str(dict(total_paid_row._mapping)["total_paid"]))
        if total_paid_row
        else Decimal("0")
    )

    outstanding_amount = invoice_amount - total_paid

    if outstanding_amount > 0:
        await db.execute(
            text("""
                INSERT INTO payments (invoice_id, amount, payment_method, payment_date, created_by)
                VALUES (:invoice_id, :amount, :payment_method, NOW(), :created_by)
            """),
            {
                "invoice_id": invoice_id,
                "amount": outstanding_amount,
                "payment_method": "mark_paid",
                "created_by": user_id,
            },
        )

    await db.execute(
        text("UPDATE invoices SET status = 'paid' WHERE id = :invoice_id"),
        {"invoice_id": invoice_id},
    )

    await db.execute(
        text("""
            INSERT INTO invoice_status_history (invoice_id, from_status, to_status, changed_by, reason)
            VALUES (:invoice_id, :from_status, 'paid', :changed_by, :reason)
        """),
        {
            "invoice_id": invoice_id,
            "from_status": current_status,
            "changed_by": user_id,
            "reason": "Manually marked as paid",
        },
    )

    await db.commit()

    try:
        invoice_result = await db.execute(
            text("""
                SELECT i.id, i.invoice_number, i.amount, i.share_token,
                       c.email, c.name
                FROM invoices i
                JOIN clients c ON i.client_id = c.id
                WHERE i.id = :invoice_id
            """),
            {"invoice_id": invoice_id},
        )
        invoice_data = dict(invoice_result.first()._mapping)

        background_tasks.add_task(
            EmailService.send_receipt_email_with_tracking,
            invoice_id=str(invoice_id),
            to=invoice_data["email"],
            receipt_data={
                "amount": str(invoice_data["amount"]),
                "invoice_number": invoice_data["invoice_number"],
                "payment_date": str(datetime.utcnow().date()),
                "paid_amount": str(invoice_amount),
                "payment_method": "mark_paid",
                "share_token": invoice_data.get("share_token"),
                "client_name": invoice_data.get("name", "Customer"),
            },
        )
    except Exception as e:
        logger.error(f"Failed to queue receipt email: {e}")

    updated_result = await db.execute(
        text("""
            SELECT id, user_id, client_id, amount, description, due_date, status, created_at, invoice_number
            FROM invoices
            WHERE id = :invoice_id
        """),
        {"invoice_id": invoice_id},
    )

    return dict(updated_result.first()._mapping)


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download PDF for an invoice."""
    try:
        pdf_bytes, filename = await build_invoice_pdf_bytes(
            db, invoice_id=invoice_id, user_id=user_id
        )
    except ValueError:
        raise HTTPException(404, "Invoice not found")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{invoice_id}/payments/{payment_id}/receipt")
async def get_payment_receipt(
    invoice_id: UUID,
    payment_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download PDF receipt for a payment."""
    result = await db.execute(
        text("""
            SELECT
                p.id, p.amount, p.payment_method, p.payment_date,
                p.reference,
                i.id as invoice_id, i.invoice_number,
                c.name as client_name, c.email as client_email
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.id
            JOIN clients c ON i.client_id = c.id
            WHERE p.id = :payment_id AND i.id = :invoice_id AND i.user_id = :uid
        """),
        {"payment_id": payment_id, "invoice_id": invoice_id, "uid": user_id},
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Payment not found")

    data = dict(row._mapping)
    business_info = await get_business_settings(db, user_id)
    receipt_number = f"RCP-{payment_id.hex[:8].upper()}"

    pdf_bytes = PDFService.generate_receipt_pdf(
        receipt_id=str(data["id"]),
        receipt_number=receipt_number,
        invoice_id=str(data["invoice_id"]),
        invoice_number=data.get("invoice_number"),
        amount=Decimal(str(data["amount"])),
        payment_method=data.get("payment_method", "bank_transfer"),
        payment_date=data["payment_date"],
        client_name=data["client_name"],
        client_email=data["client_email"],
        business_info=business_info,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={receipt_number}.pdf"},
    )
