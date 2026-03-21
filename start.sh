#!/bin/sh
# Always replace the volume DB with the bundled copy if present and FORCE_DB_SEED is set
if [ "$FORCE_DB_SEED" = "1" ] && [ -f /app/data/reepo.db ]; then
  echo "Force-seeding /data/reepo.db from bundled copy..."
  cp -f /app/data/reepo.db /data/reepo.db
elif [ ! -s /data/reepo.db ] && [ -f /app/data/reepo.db ]; then
  echo "Seeding /data/reepo.db from bundled copy..."
  cp /app/data/reepo.db /data/reepo.db
elif [ ! -s /data/reepo.db ]; then
  echo "WARNING: /data/reepo.db not found. Ensure the volume is mounted."
fi
exec uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8000}
