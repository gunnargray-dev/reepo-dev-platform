#!/bin/sh
if [ ! -s /data/reepo.db ]; then
  echo "WARNING: /data/reepo.db not found. Ensure the volume is mounted."
fi
exec uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8000}
