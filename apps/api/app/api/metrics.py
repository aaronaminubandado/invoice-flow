from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID
from typing import Optional

from app.deps import get_current_user
from app.core.database import get_db
from app.services.export import generate_csv, generate_xlsx, generate_pdf_table

router = APIRouter(prefix="/metrics", tags=["Metrics"])

METRICS_HEADERS = [
    "Month",
    "Total Invoiced",
    "Total Paid",
    "Total Outstanding",
    "Total Overdue",
    "Paid Invoices",
    "Outstanding Invoices",
]


@router.get("/revenue-summary")
async def revenue_summary(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get revenue summary metrics."""
    result = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(amount), 0)::NUMERIC(12,2) AS total_revenue,
                COALESCE(SUM(amount) FILTER (WHERE status = 'paid'), 0)::NUMERIC(12,2) AS total_paid,
                COALESCE(SUM(amount) FILTER (WHERE status IN ('sent', 'overdue', 'partial')), 0)::NUMERIC(12,2) AS total_outstanding,
                COALESCE(SUM(amount) FILTER (WHERE status = 'overdue'), 0)::NUMERIC(12,2) AS total_overdue
            FROM invoices
            WHERE user_id = :uid
        """),
        {"uid": user_id},
    )

    row = result.first()
    if row is None:
        return {
            "total_revenue": "0.00",
            "total_paid": "0.00",
            "total_outstanding": "0.00",
            "total_overdue": "0.00",
        }

    data = dict(row._mapping)
    return {
        "total_revenue": str(data["total_revenue"]),
        "total_paid": str(data["total_paid"]),
        "total_outstanding": str(data["total_outstanding"]),
        "total_overdue": str(data["total_overdue"]),
    }


@router.get("/monthly-revenue")
async def monthly_revenue(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get monthly revenue breakdown for the last 12 months."""
    result = await db.execute(
        text("""
            SELECT
                TO_CHAR(DATE_TRUNC('month', created_at), 'YYYY-MM') AS month,
                COALESCE(SUM(amount) FILTER (WHERE status = 'paid'), 0) AS paid,
                COALESCE(SUM(amount) FILTER (WHERE status IN ('sent', 'overdue', 'partial')), 0) AS outstanding
            FROM invoices
            WHERE user_id = :uid
              AND created_at >= DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month DESC
        """),
        {"uid": user_id},
    )

    rows = result.fetchall()
    if not rows:
        return []
    return [dict(row._mapping) for row in rows]


@router.get("/export")
async def export_metrics(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    format: Optional[str] = Query("csv", regex="^(csv|xlsx|pdf)$"),
):
    """Export metrics summary as CSV, Excel, or PDF."""
    result = await db.execute(
        text("""
            SELECT
                TO_CHAR(DATE_TRUNC('month', created_at), 'YYYY-MM') AS month,
                COALESCE(SUM(amount), 0) AS total_invoiced,
                COALESCE(SUM(amount) FILTER (WHERE status = 'paid'), 0) AS total_paid,
                COALESCE(SUM(amount) FILTER (WHERE status IN ('sent', 'overdue', 'partial')), 0) AS total_outstanding,
                COALESCE(SUM(amount) FILTER (WHERE status = 'overdue'), 0) AS total_overdue,
                COUNT(*) FILTER (WHERE status = 'paid') AS paid_count,
                COUNT(*) FILTER (WHERE status IN ('sent', 'overdue', 'partial')) AS outstanding_count
            FROM invoices
            WHERE user_id = :uid
              AND created_at >= DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month DESC
        """),
        {"uid": user_id},
    )

    rows_raw = result.fetchall()

    rows = []
    for row in rows_raw:
        data = dict(row._mapping)
        rows.append([
            data.get("month", ""),
            str(data.get("total_invoiced", "")),
            str(data.get("total_paid", "")),
            str(data.get("total_outstanding", "")),
            str(data.get("total_overdue", "")),
            str(data.get("paid_count", "")),
            str(data.get("outstanding_count", "")),
        ])

    if not rows:
        if format == "csv":
            return Response(
                content="No metrics data to export",
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=metrics.csv"},
            )
        raise HTTPException(404, "No metrics data to export")

    if format == "xlsx":
        content = generate_xlsx(METRICS_HEADERS, rows, sheet_name="Metrics")
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=metrics.xlsx"},
        )

    if format == "pdf":
        content = generate_pdf_table(METRICS_HEADERS, rows, title="Metrics Export")
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=metrics.pdf"},
        )

    content = generate_csv(METRICS_HEADERS, rows)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=metrics.csv"},
    )
