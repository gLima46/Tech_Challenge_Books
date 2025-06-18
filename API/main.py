from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from routes import router as book_router
from auth import router as auth_router
from ml_routes import router as ml_router

app = FastAPI(
    title="API de Livros", 
    version="1.0"
)

@app.get("/")
async def home():
    return "welcome to the books api!"

app.include_router(book_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(ml_router, prefix="/api/v1")
