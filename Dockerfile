FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY data/reepo.db /seed/reepo.db

ENV REEPO_DB_PATH=/data/reepo.db

EXPOSE 8000

COPY <<'EOF' /app/start.sh
#!/bin/sh
if [ ! -f /data/reepo.db ]; then
  cp /seed/reepo.db /data/reepo.db
  echo "Seeded database from image"
fi
exec uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8000}
EOF
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
