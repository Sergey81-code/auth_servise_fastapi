from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

import settings

engine = create_async_engine(settings.REAL_DATABASE_URL, future=True, echo=False)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session():
    """Dependency for getting async session"""
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()
