FROM python:3.14.0-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/serdial21

COPY requirements.lock pyproject.toml README.md ./
RUN python -m pip install --no-cache-dir --requirement requirements.lock

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
RUN python -m pip install --no-cache-dir --no-deps . \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin serdial21

COPY --chmod=0555 deploy/api/entrypoint.sh /usr/local/bin/serdial21-entrypoint

USER 10001:10001
ENTRYPOINT ["/usr/local/bin/serdial21-entrypoint"]
CMD ["python", "-m", "uvicorn", "serdial21.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
