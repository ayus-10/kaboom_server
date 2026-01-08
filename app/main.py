from fastapi import FastAPI
from app.modules.users.controller import router as users_router

app = FastAPI()

app.include_router(users_router, prefix="/users")
