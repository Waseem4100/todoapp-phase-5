from sqlmodel import create_engine
from sqlalchemy.pool import QueuePool
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use environment variable for database URL, with SQLite as fallback for local development
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # For Hugging Face Spaces, we should warn about SQLite limitations
    if os.getenv("SPACE_ID"):  # Hugging Face Space environment variable
        logger.warning("WARNING: Using SQLite in Hugging Face Space. Consider using PostgreSQL for production.")
        # Use a location that might be more reliable in Hugging Face Spaces
        DATABASE_URL = "sqlite:////tmp/todo_test.db"  # Use absolute path in temp directory
    else:
        DATABASE_URL = "sqlite:///./todo_test.db"

logger.info(f"Using database URL: {DATABASE_URL}")

if "postgres" in DATABASE_URL.lower():
    logger.info("Configuring PostgreSQL engine")
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,  # Smaller pool size for Neon
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 10,
        }
    )
else:
    logger.info("Configuring SQLite engine")
    engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    from sqlmodel import Session
    with Session(engine) as session:
        yield session