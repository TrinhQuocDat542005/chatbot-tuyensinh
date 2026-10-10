FROM python:3.10-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY web ./web
COPY scripts/serve_web.py ./scripts/serve_web.py
COPY actions/data/nganh.json ./actions/data/nganh.json
CMD ["python", "scripts/serve_web.py", "--host", "0.0.0.0", "--port", "8686"]
