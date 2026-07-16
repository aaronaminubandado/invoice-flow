import logging
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class InvoiceNumberService:
    @staticmethod
    async def generate_invoice_number(
        db: AsyncSession, user_id: UUID, prefix: str = "INV"
    ) -> str:
        """
        Generate a sequential, concurrency-safe invoice number.
        Uses SELECT FOR UPDATE to lock the sequence row during update,
        preventing race conditions in concurrent invoice creation.
        """
        try:
            result = await db.execute(
                text("""
                    SELECT id, last_number, prefix
                    FROM invoice_number_sequence
                    WHERE user_id = :user_id AND prefix = :prefix
                    FOR UPDATE
                """),
                {"user_id": user_id, "prefix": prefix},
            )

            row = result.fetchone()

            if row is None:
                await db.execute(
                    text("""
                        INSERT INTO invoice_number_sequence (user_id, prefix, last_number)
                        VALUES (:user_id, :prefix, 0)
                        RETURNING id, last_number, prefix
                    """),
                    {"user_id": user_id, "prefix": prefix},
                )

                result = await db.execute(
                    text("""
                        SELECT id, last_number, prefix
                        FROM invoice_number_sequence
                        WHERE user_id = :user_id AND prefix = :prefix
                        FOR UPDATE
                    """),
                    {"user_id": user_id, "prefix": prefix},
                )
                row = result.fetchone()

            new_number = row.last_number + 1

            await db.execute(
                text("""
                    UPDATE invoice_number_sequence
                    SET last_number = :new_number, updated_at = NOW()
                    WHERE user_id = :user_id AND prefix = :prefix
                """),
                {"user_id": user_id, "prefix": prefix, "new_number": new_number},
            )

            invoice_number = f"{prefix}-{new_number:06d}"

            logger.info(f"Generated invoice number {invoice_number} for user {user_id}")

            return invoice_number

        except Exception as e:
            logger.error(f"Error generating invoice number: {e}")
            raise

    @staticmethod
    async def get_next_invoice_number(
        db: AsyncSession, user_id: UUID, prefix: str = "INV"
    ) -> str:
        """
        Peek at the next invoice number without incrementing.
        Useful for preview purposes.
        """
        result = await db.execute(
            text("""
                SELECT last_number, prefix
                FROM invoice_number_sequence
                WHERE user_id = :user_id AND prefix = :prefix
            """),
            {"user_id": user_id, "prefix": prefix},
        )

        row = result.fetchone()
        next_number = (row.last_number + 1) if row else 1

        return f"{prefix}-{next_number:06d}"
