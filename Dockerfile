FROM python:3.10-slim-bookworm
ENV PYTHONUTF8=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RASA_TELEMETRY_ENABLED=false \
    TF_NUM_INTRAOP_THREADS=2 \
    TF_NUM_INTEROP_THREADS=2
WORKDIR /app
COPY requirements-lock.linux.txt ./
# This stack predates strict metadata handling in newer pip releases.
RUN python -m pip install --no-cache-dir pip==24.0 \
    && python -m pip install --no-cache-dir -r requirements-lock.linux.txt \
    && python -m pip check
COPY . .
CMD ["python", "-m", "rasa", "--version"]
