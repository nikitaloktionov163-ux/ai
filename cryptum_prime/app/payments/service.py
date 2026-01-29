from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Payment, PaymentStatus, SubscriptionTier
from app.payments.nowpayments import NowPaymentsClient
from app.payments.providers import PaymentRequest, get_provider


class PaymentService:
    async def create_payment(
        self,
        session: AsyncSession,
        user_id: int,
        amount: float,
        currency: str,
        description: str,
        tier: SubscriptionTier,
        billing_cycle: str,
    ) -> Payment:
        settings = get_settings()
        if settings.payment_provider == "nowpayments":
            payment = Payment(
                user_id=user_id,
                provider="NOWPAYMENTS",
                amount=amount,
                currency=currency,
                address=None,
                network=None,
                status=PaymentStatus.PENDING,
                tier=tier,
                billing_cycle=billing_cycle,
            )
            session.add(payment)
            await session.commit()
            await session.refresh(payment)

            client = NowPaymentsClient()
            invoice = await client.create_invoice(
                amount=amount,
                price_currency="usd",
                pay_currency=settings.payment_pay_currency,
                order_id=str(payment.id),
                description=description,
                ipn_callback_url=f"{settings.public_base_url}/payments/ipn",
            )
            payment.provider_payment_id = invoice.payment_id or None
            payment.invoice_url = invoice.invoice_url
            payment.address = invoice.pay_address
            payment.network = invoice.pay_currency
            await session.commit()
            await session.refresh(payment)
            return payment

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
            tier=tier,
            billing_cycle=billing_cycle,
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment

    async def confirm_payment(self, session: AsyncSession, payment: Payment) -> Payment:
        payment.status = PaymentStatus.CONFIRMED
        payment.confirmed_at = datetime.utcnow()
        await session.commit()
        await session.refresh(payment)
        return payment
