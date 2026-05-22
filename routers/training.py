from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.training_service import TrainingService
from models.models import TrainingJob
from schemas.training import TrainingStartRequest, TrainingResponse, TrainingStatusResponse
from utils.db import get_db
import uuid

router = APIRouter()

@router.post("/start/{upload_id}", response_model=TrainingResponse)
async def start_training(
    upload_id: str,
    request: TrainingStartRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    
    job = TrainingJob(
        id=job_id,
        upload_id=upload_id,
        status="pending",
        target_column=request.target_column
    )
    session.add(job)
    await session.commit()
    
    training_service = TrainingService(session)
    background_tasks.add_task(
        training_service.train_random_forest,
        upload_id,
        job_id,
        request.target_column
    )
    
    return TrainingResponse(
        job_id=job_id,
        upload_id=upload_id,
        status="pending"
    )

@router.get("/status/{job_id}", response_model=TrainingStatusResponse)
async def get_training_status(
    job_id: str,
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(TrainingJob).where(TrainingJob.id == job_id))
    job = result.scalars().first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return TrainingStatusResponse(
        job_id=job.id,
        status=job.status,
        accuracy=job.accuracy,
        features_used=job.features_used,
        completed_at=job.completed_at,
        mse=job.mse
    )