from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.upload_service import UploadService
from schemas.upload import UploadResponse
from utils.db import get_db
from models.models import Upload
import uuid
import pandas as pd
from io import StringIO

router = APIRouter()

@router.post("/file", response_model=UploadResponse)  
async def upload_file(
    file: UploadFile,
    session: AsyncSession = Depends(get_db)
):
    service = UploadService(session)
    upload_id = str(uuid.uuid4())

    content = await file.read()
    df = pd.read_csv(StringIO(content.decode('utf-8')))
    
    result = await service.save_file(file, upload_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    upload = Upload(
        id=upload_id,
        filename=file.filename,
        file_path=result["path"],
        rows_count=len(df),
        columns=",".join(df.columns.tolist())  
    )
    session.add(upload)

    await service.save_rows_to_db(upload_id, df.to_dict('records'))
    await session.commit()

    preview_rows = df.head(5).values.tolist() 

    return {
        "upload_id": upload_id,  
        "filename": file.filename,
        "rows_count": len(df),
        "columns": df.columns.tolist(),
        "statistics": df.describe().to_dict(),  
        "preview": preview_rows   
    }