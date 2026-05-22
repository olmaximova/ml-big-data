from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.visualization_service import VisualizationService
from utils.db import get_db
from models.models import Upload, TrainingJob

router = APIRouter()

@router.get("/chart-data/{upload_id}")
async def get_chart_data(
    upload_id: str,
    session: AsyncSession = Depends(get_db)  
):
    result = await session.execute(select(Upload).where(Upload.id == upload_id))
    upload = result.scalars().first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    service = VisualizationService(session)
    stats = await service.get_data_statistics(upload_id)
    
    return stats


@router.get("/model-metrics/{job_id}")
async def get_model_metrics(
    job_id: str,
    session: AsyncSession = Depends(get_db)  
):
    result = await session.execute(select(TrainingJob).where(TrainingJob.id == job_id))
    job = result.scalars().first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "accuracy": job.accuracy or 0,
        "mse": job.mse or 0,
        "features_used": job.features_used or 0,
        "status": job.status
    }

@router.get("/model-charts/{job_id}")
async def get_model_charts(
    job_id: str,
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(TrainingJob).where(TrainingJob.id == job_id))
    job = result.scalars().first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    service = VisualizationService(session)
    charts_data = await service.generate_model_charts(job_id)
    
    return charts_data