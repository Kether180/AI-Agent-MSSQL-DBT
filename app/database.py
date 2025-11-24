"""
Database Configuration

SQLAlchemy setup for SQLite (dev) or PostgreSQL (prod).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///./mssql_dbt_migration.db'
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {},
    echo=False  # Set to True for SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session for Flask
db_session = scoped_session(SessionLocal)

# Base class for models
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """Initialize the database (create all tables)"""
    from . import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {DATABASE_URL}")


def get_db():
    """
    Dependency for FastAPI endpoints.

    Usage:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Alias for compatibility
db = db_session
