"""
database.py
Initializes the SQLAlchemy engine and session factory.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# SQLite URI. Using check_same_thread=False for potential multi-threaded solver workers.
DATABASE_URL = "sqlite:///ceil_scheduler.db"

engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """
    Creates all tables dynamically based on the declarative models.
    Safe to call multiple times; will not overwrite existing data.
    """
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency generator for database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()