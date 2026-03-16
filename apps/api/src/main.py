import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.database import check_database_connection, dispose_database
from src.db.migration_runner import run_app_migrations_async
from src.db.seed.runner import run_app_seeds_async
from src.document_categories.router import router as document_categories_router
from src.documents.router import router as documents_router
from src.extraction_templates.router import router as extraction_templates_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db_ok = await check_database_connection()
    if not db_ok:
        logging.error("Database connection failed during startup")
        raise RuntimeError("Database connection failed during startup")

    await run_app_migrations_async()
    await run_app_seeds_async()
    logging.info("Database connection established and seeds ensured")

    yield
    logging.info("Shutting down application...")
    await dispose_database()
    logging.info("Database pool closed safely")


app = FastAPI(
    title="Search Agent API",
    lifespan=lifespan,
)

app.include_router(extraction_templates_router)
app.include_router(document_categories_router)
app.include_router(documents_router)


@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, bool | str]:
    db_ok = await check_database_connection()
    status = "healthy" if db_ok else "degraded"
    return {"status": status, "database": db_ok}
