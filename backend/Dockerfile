FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_DEV=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local
WORKDIR /backend

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --locked

# alembic.ini and migrations/ are part of the image so that
# `alembic upgrade head` works without a bind mount.
COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src

# The storage directory is created at startup by the storage adapter; make sure
# the unprivileged user owns it.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /backend/storage/files \
    && chown -R app:app /backend
USER app

EXPOSE 8000
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
