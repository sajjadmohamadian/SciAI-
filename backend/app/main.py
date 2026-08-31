from fastapi import FastAPI

from backend.app.core.logging import get_logger, setup_logging
from backend.app.api.analysis import router as analysis_router

setup_logging()
logger = get_logger(__name__)


app = FastAPI(
    title="SciAI",
    description="Self-hosted bibliometric analysis platform",
    version="0.1.0",
)
app.include_router(analysis_router)

@app.get("/health")
def health_check():
    logger.info("Health check requested")

    return {
        "status": "ok",
        "application": "SciAI",
        "version": "0.1.0",
    }