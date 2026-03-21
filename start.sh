#!/bin/sh
# Seed the volume DB from the bundled copy if missing
if [ ! -s /data/reepo.db ] && [ -f /app/data/reepo.db ]; then
  echo "Seeding /data/reepo.db from bundled copy..."
  cp /app/data/reepo.db /data/reepo.db
elif [ ! -s /data/reepo.db ]; then
  echo "WARNING: /data/reepo.db not found. Ensure the volume is mounted."
fi
exec uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8000}
