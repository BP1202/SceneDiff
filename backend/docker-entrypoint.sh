#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "==> SceneDiff Backend Container Initializing..."
echo "=================================================="

# 1. Wait for PostgreSQL readiness
echo "==> Checking database connectivity..."
python - <<'EOF'
import asyncio
import sys
from sqlalchemy import text
from app.db.session import async_engine

async def check_db():
    max_retries = 30
    for i in range(1, max_retries + 1):
        try:
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print("==> Database connection established successfully.")
            return True
        except Exception as exc:
            print(f"==> Waiting for database... ({i}/{max_retries}) [{type(exc).__name__}]")
            await asyncio.sleep(1)
    print("==> ERROR: Database unreachable after 30 seconds.", file=sys.stderr)
    sys.exit(1)

asyncio.run(check_db())
EOF

# 2. Run automatic database migrations
echo "==> Applying database migrations (alembic upgrade head)..."
alembic upgrade head

# 3. Hand over execution to application process (signal forwarding)
echo "==> Starting application..."
exec "$@"
