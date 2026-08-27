import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Use SQLite during automated tests
if os.getenv("TESTING") == "1":
    DATABASE_URL = "sqlite:///./test_bugflow.db"
else:
    DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/bugflow_db"


# SQLite needs this option; PostgreSQL does not
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()