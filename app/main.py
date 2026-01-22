import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.features.auth.router import router as auth_router
from app.features.conversation.router import router as conversation_router
from app.features.message.router import router as message_router
from app.features.pending_conversation.router import (
    router as pending_conversation_router,
)
from app.features.project.router import router as project_router
from app.features.user.router import router as user_router
from app.features.visitor.router import router as visitor_router
from app.features.visitor.websocket import router as visitor_ws_router
from app.features.widget.router import router as widget_router

logger = logging.getLogger()


@asynccontextmanager
async def lifespan(_app: FastAPI):
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: not recommended in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(project_router, prefix="/project", tags=["project"])
app.include_router(visitor_router, prefix="/visitor", tags=["visitor"])
app.include_router(conversation_router, prefix="/conversation", tags=["conversation"])
app.include_router(
    widget_router,
    prefix="/project/{project_id}/widget",
    tags=["widget"]
)
app.include_router(
    message_router,
    prefix="/conversation/{conversation_id}/message",
    tags=["message"]
)
app.include_router(
    pending_conversation_router,
    prefix="/pending-conversation",
    tags=["pending-conversation"]
)

app.include_router(visitor_ws_router)


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["infra"])
async def healthcheck():
    return {"status": "ok"}
