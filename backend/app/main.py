from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.analysis import router as analysis_router
from backend.app.api.dataset import router as dataset_router
from backend.app.api.project import router as project_router
from backend.app.core.logging import get_logger, setup_logging


setup_logging()
logger = get_logger(__name__)


app = FastAPI(
    title="SciAI",
    description="Self-hosted bibliometric analysis platform",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(analysis_router)
app.include_router(dataset_router)
app.include_router(project_router)


@app.get("/health")
def health_check():
    logger.info("Health check requested")

    return {
        "status": "ok",
        "application": "SciAI",
        "version": "0.1.0",
    }