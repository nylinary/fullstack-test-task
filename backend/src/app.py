"""Точка входа ASGI (``uvicorn src.app:app``)."""

from src.presentation.http.app import create_app

app = create_app()
