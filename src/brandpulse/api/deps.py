"""FastAPI dependencies.

The session dependency yields one transactional session per request and is the
single seam tests override to point at an isolated in-memory database.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from brandpulse.db.engine import session_scope


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_scope() as session:
        yield session
