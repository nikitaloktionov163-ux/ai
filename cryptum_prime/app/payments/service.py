from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Payment, PaymentStatus
from app.payments.providers import PaymentRequest, get_provider


class PaymentService:
    async def create_payment(
        self,
        session: AsyncSession,
        user_id: int,
        amount: float,
        currency: str,
        description: str,
    ) -> Payment:
        provider = get_provider()
        response = await provider.create_payment(
            PaymentRequest(amount=amount, currency=currency, description=description)
        )
        payment = Payment(
            user_id=user_id,
            provider=provider.__class__.__name__,
            amount=amount,
            currency=currency,
            address=response.address,
            network=response.network,
            status=PaymentStatus.PENDING,
            metadata=response.provider_reference,
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment

    async def confirm_payment(self, session: AsyncSession, payment: Payment) -> Payment:
        payment.status = PaymentStatus.CONFIRMED
        await session.commit()
        await session.refresh(payment)
        return payment
