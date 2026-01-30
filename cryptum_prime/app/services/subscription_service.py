from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Subscription, SubscriptionStatus, SubscriptionTier


class SubscriptionService:
    async def get_active(self, session: AsyncSession, user_id: int) -> Subscription | None:
        result = await session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
        )
        return result.scalar_one_or_none()

    async def create_pending(self, session: AsyncSession, user_id: int, tier: SubscriptionTier) -> Subscription:
        subscription = Subscription(user_id=user_id, tier=tier, status=SubscriptionStatus.PENDING)
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def activate(self, session: AsyncSession, subscription: Subscription, months: int) -> Subscription:
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.start_at = datetime.utcnow()
        subscription.end_at = subscription.start_at + timedelta(days=30 * months)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def activate_for_payment(
        self,
        session: AsyncSession,
        user_id: int,
        tier: SubscriptionTier,
        months: int,
    ) -> Subscription:
        active = await self.get_active(session, user_id)
        if active and active.end_at:
            active.status = SubscriptionStatus.ACTIVE
            active.tier = tier
            active.end_at = active.end_at + timedelta(days=30 * months)
            await session.commit()
            await session.refresh(active)
            return active

        subscription = await self.create_pending(session, user_id=user_id, tier=tier)
        return await self.activate(session, subscription, months=months)

    async def expire(self, session: AsyncSession, subscription: Subscription) -> Subscription:
        subscription.status = SubscriptionStatus.EXPIRED
        await session.commit()
        await session.refresh(subscription)
        return subscription
