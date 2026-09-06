import asyncio
import sys
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.database import engine, Base
import app.models.entities
import app.models.knowledge

async def main():
    print("Creating any missing tables in database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Finished creating tables.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
