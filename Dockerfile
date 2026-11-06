FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    HOST=0.0.0.0 \
    PORT=8080

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY deploy/entrypoint.sh /entrypoint.sh

RUN useradd --create-home --uid 1000 radar && mkdir -p /app/data && chown -R radar /app/data \
    && chmod +x /entrypoint.sh

EXPOSE 8080
HEALTHCHECK --interval=60s --timeout=5s --start-period=20s \
  CMD python -c "import os,urllib.request,base64;r=urllib.request.Request('http://127.0.0.1:8080/api/status');p=os.environ.get('APP_PASSWORD');p and r.add_header('Authorization','Basic '+base64.b64encode(('admin:'+p).encode()).decode());urllib.request.urlopen(r,timeout=4)"
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-c", "uvicorn app.main:app --host \"$HOST\" --port \"$PORT\""]
