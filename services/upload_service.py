from fastapi import UploadFile
import csv
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import UploadedData

class UploadService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_file(self, file: UploadFile, upload_id: str) -> dict:
        try:
            content = await file.read()
            path = f"data/{upload_id}_{file.filename}"

            with open(path, 'wb') as f:
                f.write(content)

            text = content.decode('utf-8')
            reader = csv.DictReader(text.split('\n'))
            rows = [row for row in reader if row and any(row.values())]

            return {
                "success": True,
                "path": path,
                "rows": rows         
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_rows_to_db(self, upload_id: str, rows: list):
        for row in rows:
            if row and any(row.values()):
                data_id = str(uuid.uuid4())
                uploaded_data = UploadedData(
                    id=data_id,
                    upload_id=upload_id,
                    data=json.dumps(row)
                )
                self.session.add(uploaded_data)