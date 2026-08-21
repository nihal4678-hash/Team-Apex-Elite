from collections.abc import AsyncGenerator


async def get_database() -> AsyncGenerator[None, None]:
    """Placeholder dependency for the future campus data store."""
    yield None
