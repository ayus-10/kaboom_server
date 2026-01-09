from fastapi import FastAPI
from app.modules.auth.auth_controller import router as auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
