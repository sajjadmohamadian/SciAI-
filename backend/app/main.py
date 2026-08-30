from fastapi import FastAPI

app = FastAPI(
    title="SciAI",
    description="Self-hosted bibliometric analysis platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "application": "SciAI",
        "version": "0.1.0",
    }