from fastapi import FastAPI

from backend.app.core.logging import get_logger, setup_logging


setup_logging()
logger = get_logger(__name__)


app = FastAPI(
    title="SciAI",
    description="Self-hosted bibliometric analysis platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    logger.info("Health check requested")

    return {
        "status": "ok",
        "application": "SciAI",
        "version": "0.1.0",
    }