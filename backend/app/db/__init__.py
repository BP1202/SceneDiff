"""Database package — public re-exports.

Import from here rather than from submodules to keep callers decoupled
from the internal layout.

    from app.db import Base, get_db
"""
from app.db.base import Base
from app.db.session import get_db

__all__ = ["Base", "get_db"]
