from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.core.logging import setup_logging
from app.api.routes.departments import router as departments_router

setup_logging()

app = FastAPI(title="Organization Structure API")

app.include_router(health_router)
app.include_router(departments_router)
