"""Reexporta todos os models pra ficarem registrados em Base.metadata
(usado pelo autogenerate do Alembic e por `from app.models import *`)."""
from app.models.user import User

__all__ = ["User"]
