from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import TrainingJob, UploadedData
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.impute import SimpleImputer
import pandas as pd
import json
from datetime import datetime
import asyncio

class TrainingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _update_job_status(self, job_id: str, status: str):
        try:
            result = await self.session.execute(
                select(TrainingJob).where(TrainingJob.id == job_id)
            )
            job = result.scalars().first()
            if job:
                job.status = status
                if status == "failed":
                    job.completed_at = datetime.utcnow()
                await self.session.commit()
        except Exception as e:
            await self.session.rollback()

    async def train_random_forest(self, upload_id: str, job_id: str, target_column: str):
        try:
            await self._update_job_status(job_id, "processing")
            
            result = await self.session.execute(
                select(UploadedData).where(UploadedData.upload_id == upload_id)
            )
            rows = result.scalars().all()
            if not rows:
                await self._update_job_status(job_id, "failed")
                return
            
            df = pd.DataFrame([json.loads(row.data) for row in rows])
            
            if target_column not in df.columns:
                await self._update_job_status(job_id, "failed")
                return
            
            numeric_df = df.select_dtypes(include=['number']).copy()
            
            if target_column not in numeric_df.columns:
                await self._update_job_status(job_id, "failed")
                return
            
            numeric_df = numeric_df.dropna(subset=[target_column])
            
            y = numeric_df[target_column]
            X = numeric_df.drop(columns=[target_column])
            
            if X.shape[1] < 1 or len(X) < 10:
                await self._update_job_status(job_id, "failed")
                return
            
            imputer = SimpleImputer(strategy='mean')
            X = await asyncio.to_thread(imputer.fit_transform, X)
            X = pd.DataFrame(X, columns=numeric_df.drop(columns=[target_column]).columns)
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            await asyncio.to_thread(model.fit, X_train, y_train)
            
            y_pred = await asyncio.to_thread(model.predict, X_test)
            accuracy = r2_score(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            
            result = await self.session.execute(
                select(TrainingJob).where(TrainingJob.id == job_id)
            )
            job = result.scalars().first()
            if job:
                job.status = "completed"
                job.accuracy = accuracy
                job.mse = mse
                job.features_used = X.shape[1]
                job.completed_at = datetime.now()
                await self.session.commit()
                
        except Exception as e:
            await self._update_job_status(job_id, "failed")
