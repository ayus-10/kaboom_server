from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine
from app.features.auth.auth_router import router as auth_router
from app.features.users.user_router import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting application")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
        logging.info("Database connection established")
    except Exception:
        logging.exception("Database connection failed")
        raise

    yield

    logging.info("Shutting down application")
    await engine.dispose()
    logging.info("Database engine disposed")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/users", tags=["users"])


@app.get("/health", tags=["infra"])
async def healthcheck():
    return {"status": "ok"}
