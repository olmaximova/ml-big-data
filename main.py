import os
import uvicorn
from fastapi import FastAPI, File, UploadFile
import uvicorn

app = FastAPI()
UPLOAD_DIR = "uploads" 
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(uploaded_file: UploadFile):
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.filename)
    
    with open(file_path, "wb") as f:
        f.write(await uploaded_file.read())
    
    return {"path": file_path}

if __name__=="__main__":
    uvicorn.run("main:app", reload=True)