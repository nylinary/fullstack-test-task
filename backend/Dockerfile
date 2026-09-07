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

# alembic.ini и migrations/ лежат в образе, чтобы `alembic upgrade head`
# работал без bind mount'а.
COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src

# Директорию хранилища создаёт при старте адаптер; следим, чтобы она
# принадлежала непривилегированному пользователю.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /backend/storage/files \
    && chown -R app:app /backend
USER app

EXPOSE 8000
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
