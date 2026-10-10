import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
import logging
from app.database import engine, Base
from scripts.seed_demo_users import seed_users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_and_seed")

async def init_and_seed():
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Seeding default law enforcement demo accounts & initial docket...")
    await seed_users()
    await engine.dispose()
    logger.info("Database initialization and seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(init_and_seed())
