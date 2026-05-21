from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from routers import upload, training, visualization
from utils.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="приложение для работы с большими данными", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(visualization.router, prefix="/api/visualization", tags=["visualization"])

@app.get("/")
async def root():
    return FileResponse(Path("static/index.html"))