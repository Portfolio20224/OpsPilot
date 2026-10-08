from dotenv import load_dotenv
load_dotenv()  
import logging

from fastapi import FastAPI

from app.api.routes import analysis_router, router

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "level=%(levelname)s "
        "logger=%(name)s "
        "message=%(message)s"
    ),
)


app = FastAPI(
    title="OpsPilot",
    description="AI-powered incident response assistant",
    version="0.1.0",
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "opspilot",
    }

app.include_router(router)
app.include_router(analysis_router)