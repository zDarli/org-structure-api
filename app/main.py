from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="Organization Structure API")

app.include_router(health_router)
