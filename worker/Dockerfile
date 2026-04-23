# Stage 1 — builder

FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY worker/requirements.txt .

RUN pip install --upgrade pip \
 && pip install --prefix=/install -r requirements.txt



# Stage 2 — runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/install/lib/python3.12/site-packages

COPY --from=builder /install /install
COPY worker/worker.py .

RUN addgroup --system appgroup \
 && adduser  --system --ingroup appgroup --no-create-home appuser

USER appuser

# Health check: verify the worker process is alive and can reach Redis.
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "\
import os, redis; \
r = redis.Redis(host=os.getenv('REDIS_HOST','localhost'), port=int(os.getenv('REDIS_PORT',6379)), password=os.getenv('REDIS_PASSWORD')); \
r.ping()"

CMD ["python", "worker.py"]