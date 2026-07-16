from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.deps import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def dashboard_stats(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Aggregated invoice stats for dashboard consumption.
    """
    result = await db.execute(text(
        """
        SELECT
          COALESCE(SUM(amount) FILTER (WHERE status='sent'), 0) AS total_invoiced,
          COALESCE(SUM(amount) FILTER (WHERE status='paid'), 0) AS total_paid,
          COALESCE(SUM(amount) FILTER (WHERE status='overdue'), 0) AS total_overdue
        FROM invoices
        WHERE user_id = :uid
        """),
        {"uid": user_id},
    )

    row = result.first()
    if row is None:
        return {
            "total_invoiced": 0,
            "total_paid": 0,
            "total_overdue": 0
        }
    return dict(row._mapping)
