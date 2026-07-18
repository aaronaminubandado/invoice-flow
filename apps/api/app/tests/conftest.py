import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from app.main import app
from app.core.config import settings
from uuid import uuid4


def _database_url() -> str:
    url = (settings.TEST_DATABASE_URL or "").strip()
    if not url:
        pytest.exit(
            "TEST_DATABASE_URL must be set for tests. "
            "Refusing to fall back to DATABASE_URL to protect production data."
        )
    return url


TEST_DATABASE_URL = _database_url()

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        schema_ready = await connection.scalar(
            text("SELECT to_regclass('public.users')")
        )
        if schema_ready is None:
            pytest.fail(
                "Test database is not migrated. Run "
                "`python scripts/prepare_test_db.py` before pytest."
            )

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            if transaction.is_active:
                await transaction.rollback()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    user_id = uuid4()
    await db_session.execute(
        text("INSERT INTO users (id) VALUES (:id) ON CONFLICT DO NOTHING"),
        {"id": user_id},
    )
    await db_session.commit()
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


@pytest_asyncio.fixture
async def unauthenticated_client(db_session: AsyncSession):
    from app.core.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def user_id(test_user: uuid4):
    return test_user
