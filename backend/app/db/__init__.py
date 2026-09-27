"""Database package.

Sub-modules
-----------
app.db.base     — DeclarativeBase (Base)
app.db.session  — async engine, session factory, get_db dependency

Preferred import style for callers:

    from app.db.base import Base
    from app.db.session import get_db, async_engine

Importing from the sub-modules directly (rather than from app.db) avoids
triggering the engine initialisation in session.py when only Base is needed
(e.g. in Alembic env.py).
"""
