#!/usr/bin/env bash
set -euo pipefail

# App and Litestream must agree on where the SQLite file lives.
export DB_PATH="${DB_PATH:-data/rmeti_portal.db}"
mkdir -p "$(dirname "$DB_PATH")"

# 1) Restore the most recent copy from R2. On the very first deploy there is
#    no replica yet, so -if-replica-exists makes this a safe no-op.
echo "[start] Restoring database from R2 (if a backup exists)..."
./litestream restore -config litestream.yml -if-replica-exists "$DB_PATH"

# 2) Launch the app *under* Litestream so every committed write streams to R2.
#    --workers 1 keeps a single SQLite writer and a consistent rate limiter.
echo "[start] Launching app under Litestream..."
exec ./litestream replicate -config litestream.yml \
  -exec "gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 1"
