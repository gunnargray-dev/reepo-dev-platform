FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY data/ data/
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV REEPO_DB_PATH=/data/reepo.db

EXPOSE 8000

CMD ["/app/start.sh"]
