"""Apply every SQL migration to the configured test database."""

import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv


API_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = API_ROOT / "migrations"


def get_test_database_url() -> str:
    load_dotenv(API_ROOT / ".env")
    url = os.getenv("TEST_DATABASE_URL", "").strip()
    if not url:
        raise SystemExit(
            "TEST_DATABASE_URL is required. Refusing to use DATABASE_URL."
        )
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def main() -> None:
    connection = await asyncpg.connect(get_test_database_url())
    try:
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            await connection.execute(migration.read_text())
            print(f"Applied {migration.name}")
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
