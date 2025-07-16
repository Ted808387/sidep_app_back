from fastapi import FastAPI
from database import engine, Base
import models

app = FastAPI()

# 創建所有資料庫表格
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def read_root():
    return {"message": "Hello from FastAPI backend!"}
