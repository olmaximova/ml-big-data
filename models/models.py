from sqlalchemy import Column, String, DateTime, Integer, Text, Float
from datetime import datetime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    status = Column(String, default="completed")
    rows_count = Column(Integer, default=0)
    columns = Column(Text, nullable=True) 
    created_at = Column(DateTime, default=datetime.now)

class UploadedData(Base):
    __tablename__ = "uploaded_data"
    id = Column(String, primary_key=True)
    upload_id = Column(String)
    data = Column(Text)

class TrainingJob(Base):
    __tablename__ = "training_jobs"
    id = Column(String, primary_key=True)
    upload_id = Column(String)
    target_column = Column(String, nullable=True)
    status = Column(String, default="pending")
    accuracy = Column(Float, nullable=True)
    mse = Column(Float, nullable=True)
    features_used = Column(Integer, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)