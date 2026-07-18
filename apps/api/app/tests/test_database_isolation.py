from uuid import UUID

import pytest
from sqlalchemy import text


ISOLATION_USER_ID = UUID("00000000-0000-0000-0000-000000000042")


@pytest.mark.asyncio
async def test_01_committed_test_data_is_scoped_to_test(db_session):
    await db_session.execute(
        text("INSERT INTO users (id) VALUES (:id) ON CONFLICT DO NOTHING"),
        {"id": ISOLATION_USER_ID},
    )
    await db_session.commit()

    exists = await db_session.scalar(
        text("SELECT EXISTS(SELECT 1 FROM users WHERE id = :id)"),
        {"id": ISOLATION_USER_ID},
    )
    assert exists is True


@pytest.mark.asyncio
async def test_02_previous_test_commit_was_rolled_back(db_session):
    exists = await db_session.scalar(
        text("SELECT EXISTS(SELECT 1 FROM users WHERE id = :id)"),
        {"id": ISOLATION_USER_ID},
    )
    assert exists is False
