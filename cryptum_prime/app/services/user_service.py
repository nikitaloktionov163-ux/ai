from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserService:
    async def get_or_create(self, session: AsyncSession, telegram_id: int, username: str | None) -> User:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            return user
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def update_language(self, session: AsyncSession, user: User, language: str) -> User:
        user.language = language
        await session.commit()
        await session.refresh(user)
        return user

    async def update_exchange(self, session: AsyncSession, user: User, exchange: str) -> User:
        user.exchange = exchange
        await session.commit()
        await session.refresh(user)
        return user
