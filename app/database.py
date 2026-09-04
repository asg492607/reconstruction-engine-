from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path
from app.config import settings

# If using local sqlite, ensure target dir exists
if "sqlite" in settings.DATABASE_URL:
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    if "./" in db_path:
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
