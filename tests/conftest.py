import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base, get_db
from app.main import app
from app.auth.security import hash_password
from app.models.entities import User, Organization
from app.models.enums import Role, Department

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def seed_users(db_session: AsyncSession):
    org = Organization(name="Metropolitan Police Department")
    db_session.add(org)
    await db_session.flush()

    admin = User(
        email="admin@police.gov",
        hashed_password=hash_password("adminpass123"),
        full_name="Chief Admin",
        role=Role.ADMIN,
        department=Department.ADMIN,
        organization_id=org.id,
        is_active=True
    )
    lead = User(
        email="lead@police.gov",
        hashed_password=hash_password("leadpass123"),
        full_name="Lead Investigator Roy",
        role=Role.LEAD_INVESTIGATOR,
        department=Department.INVESTIGATION,
        organization_id=org.id,
        is_active=True
    )
    investigator = User(
        email="investigator@police.gov",
        hashed_password=hash_password("invpass123"),
        full_name="Detective Sarah",
        role=Role.INVESTIGATOR,
        department=Department.INVESTIGATION,
        organization_id=org.id,
        is_active=True
    )
    forensic = User(
        email="forensic@police.gov",
        hashed_password=hash_password("forensicpass123"),
        full_name="Forensic Officer Chen",
        role=Role.FORENSIC_OFFICER,
        department=Department.FORENSIC,
        organization_id=org.id,
        is_active=True
    )
    financial = User(
        email="financial@police.gov",
        hashed_password=hash_password("finpass123"),
        full_name="Financial Analyst David",
        role=Role.FINANCIAL_ANALYST,
        department=Department.FINANCIAL,
        organization_id=org.id,
        is_active=True
    )
    unassigned = User(
        email="outsider@police.gov",
        hashed_password=hash_password("outsider123"),
        full_name="Outsider Officer",
        role=Role.INVESTIGATOR,
        department=Department.INVESTIGATION,
        organization_id=org.id,
        is_active=True
    )

    db_session.add_all([admin, lead, investigator, forensic, financial, unassigned])
    await db_session.commit()

    return {
        "admin": admin,
        "lead": lead,
        "investigator": investigator,
        "forensic": forensic,
        "financial": financial,
        "unassigned": unassigned,
    }
