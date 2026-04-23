
# Stage 1 — builder
# Install dependencies into an isolated prefix so only the wheels (no pip /
# setuptools / build caches) land in the final image.
FROM python:3.12-slim AS builder

WORKDIR /app

# Keeps bytecode out of the source tree and disables the pip version nag
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY api/requirements.txt .

RUN pip install --upgrade pip \
 && pip install --prefix=/install -r requirements.txt


# Stage 2 — runtime
# Lean image: no compiler, no pip, no build artefacts.

FROM python:3.12-slim AS runtime

WORKDIR /builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Tell Python where the dependencies were installed
    PYTHONPATH=/install/lib/python3.12/site-packages

# Pull only the installed packages from the builder stage
COPY --from=builder /install /install

# Copy application source — explicitly, so no .env or secrets slip in
COPY api/main.py .

# Create a non-root user and group with no login shell
RUN addgroup --system appgroup \
 && adduser  --system --ingroup appgroup --no-create-home appuser

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')"

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]