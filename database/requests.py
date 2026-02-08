from database.core import async_session
from database.models import User, ConversionLog
from sqlalchemy import select
from sqlalchemy import func


async def set_user(tg_id: int, username: str, full_name: str):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            session.add(User(tg_id=tg_id, username=username, full_name=full_name))
            await session.commit()

async def log_conversion(tg_id: int, file_type: str):
    async with async_session() as session:
        session.add(ConversionLog(user_id=tg_id, file_type=file_type))
        await session.commit()

async def get_stats():
    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        conversion_count = await session.scalar(select(func.count(ConversionLog.id)))
        return users_count, conversion_count