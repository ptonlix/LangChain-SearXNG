"""FastAPI app creation, logger configuration and main API routes."""

from langchain_searxng.di import global_injector
from langchain_searxng.launcher import create_app

app = create_app(global_injector)
