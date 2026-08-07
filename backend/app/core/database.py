"""Engine e sessão do SQLAlchemy, configurados para SQLite."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# check_same_thread=False é necessário pro SQLite funcionar com o FastAPI
# (cada request pode ser tratada numa thread diferente)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI: entrega uma sessão de banco e garante que fecha depois."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
