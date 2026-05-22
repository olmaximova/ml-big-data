from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import UploadedData, TrainingJob
import json
import pandas as pd
import json
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

class VisualizationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_data_statistics(self, upload_id: str) -> dict:
        result = await self.session.execute(
            select(UploadedData).where(UploadedData.upload_id == upload_id)
        )
        rows = result.scalars().all()
        
        if not rows:
            return {"columns": [], "statistics": {}}
        
        data_list = [json.loads(row.data) for row in rows]
        df = pd.DataFrame(data_list)
        
        numeric_df = df.select_dtypes(include=['number'])
        
        columns = numeric_df.columns.tolist()
        statistics = {}
        
        for col in columns:
            mean_val = numeric_df[col].mean()
            std_val = numeric_df[col].std()
            statistics[col] = {
                "mean": float(mean_val) if pd.notna(mean_val) else 0,
                "std": float(std_val) if pd.notna(std_val) else 0
            }
        
        return {"columns": columns, "statistics": statistics}

    async def generate_model_charts(self, job_id: str) -> dict:
        result = await self.session.execute(
            select(TrainingJob).where(TrainingJob.id == job_id)
        )
        job = result.scalars().first()
        
        if not job or not job.upload_id:
            return {}
        
        data_result = await self.session.execute(
            select(UploadedData).where(UploadedData.upload_id == job.upload_id)
        )
        rows = data_result.scalars().all()
        
        if not rows:
            return {}
    
        
        df = pd.DataFrame([json.loads(row.data) for row in rows])
        numeric_df = df.select_dtypes(include=['number'])
        
        if job.target_column not in numeric_df.columns:
            return {}
        
        numeric_df = numeric_df.dropna(subset=[job.target_column])
        
        y = numeric_df[job.target_column]
        X = numeric_df.drop(columns=[job.target_column])
        
        if X.shape[1] < 1 or len(X) < 10:
            return {}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        residuals = (y_test - y_pred).tolist()
        
        feature_importance = {
            "columns": X.columns.tolist(),
            "values": model.feature_importances_.tolist()
        }
        
        return {
            "feature_importance": feature_importance,
            "actual": y_test.tolist(),
            "predicted": y_pred.tolist(),
            "residuals": residuals
        }