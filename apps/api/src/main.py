import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.database import check_database_connection, dispose_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_ok = await check_database_connection()
    if not db_ok:
        logging.error("Database connection failed during startup")
        raise RuntimeError("Database connection failed during startup")

    logging.info("Database connection established")

    yield
    logging.info("Shutting down application...")
    await dispose_database()
    logging.info("Database pool closed safely")


app = FastAPI(
    title="Search Agent API",
    lifespan=lifespan,
)


@app.get("/api/health", tags=["health"])
async def health_check():
    db_ok = await check_database_connection()
    status = "healthy" if db_ok else "degraded"
    return {"status": status, "database": db_ok}
