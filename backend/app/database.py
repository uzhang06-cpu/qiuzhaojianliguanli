import os

# Silence SQLAlchemy 2.0 deprecation warnings when running on 1.4
os.environ.setdefault("SQLALCHEMY_SILENCE_UBER_WARNING", "1")

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args=(
        {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    ),
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session & closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
