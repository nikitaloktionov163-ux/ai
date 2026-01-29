from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.db.models import Payment, PaymentStatus, SubscriptionTier
from app.payments.service import PaymentService
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentCreateRequest(BaseModel):
    user_id: int
    tier: SubscriptionTier
    billing_cycle: str


class PaymentResponse(BaseModel):
    payment_id: int
    address: str
    network: str
    amount: float
    currency: str
    status: PaymentStatus


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payload: PaymentCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> PaymentResponse:
    pricing = {
        "PRO": {"monthly": 29, "yearly": 295},
        "PRIME": {"monthly": 79, "yearly": 758},
    }
    tier_prices = pricing.get(payload.tier.value)
    if not tier_prices:
        raise HTTPException(status_code=400, detail="Unsupported tier")
    amount = tier_prices.get(payload.billing_cycle)
    if not amount:
        raise HTTPException(status_code=400, detail="Unsupported billing cycle")

    payment_service = PaymentService()
    payment = await payment_service.create_payment(
        session,
        user_id=payload.user_id,
        amount=amount,
        currency="USDT",
        description=f"{payload.tier.value} {payload.billing_cycle}",
    )

    return PaymentResponse(
        payment_id=payment.id,
        address=payment.address,
        network=payment.network,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
    )


class PaymentConfirmRequest(BaseModel):
    payment_id: int
    months: int
    tier: SubscriptionTier


@router.post("/confirm")
async def confirm_payment(
    payload: PaymentConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    payment = await session.get(Payment, payload.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Payment already processed")

    payment_service = PaymentService()
    await payment_service.confirm_payment(session, payment)

    subscription_service = SubscriptionService()
    subscription = await subscription_service.create_pending(
        session, user_id=payment.user_id, tier=payload.tier
    )
    await subscription_service.activate(session, subscription, months=payload.months)

    return {"status": "confirmed"}
