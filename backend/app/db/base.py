"""SQLAlchemy async declarative base.

All ORM models must inherit from Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all SceneDiff ORM models."""
