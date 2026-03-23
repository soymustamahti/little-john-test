import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session_factory
from src.db.migration_runner import run_app_migrations
from src.db.seed.document_categories import seed_document_categories
from src.db.seed.extraction_templates import seed_extraction_templates


async def run_app_seeds() -> None:
    session_factory = get_async_session_factory()

    async with session_factory() as session:
        try:
            await _seed_reference_data(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def run_app_seeds_async() -> None:
    await run_app_seeds()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_app_migrations()
    await run_app_seeds()
    logging.info("Reference data seeding completed.")


async def _seed_reference_data(session: AsyncSession) -> None:
    document_category_inserts = await seed_document_categories(session)
    logging.info("Document category seeds inserted: %d", document_category_inserts)

    extraction_template_inserts = await seed_extraction_templates(session)
    logging.info("Extraction template seeds inserted: %d", extraction_template_inserts)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
