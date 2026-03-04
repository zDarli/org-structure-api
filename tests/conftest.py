from __future__ import annotations

import os
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.main import app
from app.core.db import get_db
from app.models.base import Base
from app.models.employee import Employee
from app.models.department import Department


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    # чтобы pytest-anyio работал на asyncio
    return "asyncio"


@pytest.fixture(scope="session")
async def engine() -> AsyncEngine:
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def db_session(engine: AsyncEngine) -> AsyncSession:
    session_maker = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_maker() as session:
        yield session


@pytest.fixture(autouse=True)
async def clean_db(db_session: AsyncSession) -> None:
    """
    Гарантируем изоляцию тестов.
    Быстро: чистим таблицы после каждого теста.
    """
    yield
    # порядок важен из-за FK: сначала employees, потом departments
    await db_session.execute(delete(Employee))
    await db_session.execute(delete(Department))
    await db_session.commit()


@pytest.fixture()
async def client(db_session: AsyncSession) -> AsyncClient:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
