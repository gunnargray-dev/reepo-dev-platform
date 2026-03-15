#!/bin/sh
if [ ! -s /data/reepo.db ]; then
  cp /seed/reepo.db /data/reepo.db
  echo "Seeded database from image"
fi
exec uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8000}
