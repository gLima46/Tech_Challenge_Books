from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from API.routes import router as book_router
from API.auth import router as auth_router

app = FastAPI(
    title="API de Livros", 
    version="1.0"
)

app.include_router(book_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
async def home():
    return "The home check is successful!"
