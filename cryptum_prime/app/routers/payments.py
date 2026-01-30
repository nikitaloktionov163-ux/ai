from datetime import datetime

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db_session
from app.db.models import Payment, PaymentStatus, SubscriptionTier
from app.payments.nowpayments import verify_nowpayments_signature
from app.payments.service import PaymentService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService

router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentCreateRequest(BaseModel):
    telegram_id: int
    username: str | None = None
    tier: SubscriptionTier
    billing_cycle: str


class PaymentResponse(BaseModel):
    payment_id: int
    invoice_url: str | None = None


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

    user_service = UserService()
    user = await user_service.get_or_create(
        session, telegram_id=payload.telegram_id, username=payload.username
    )

    payment_service = PaymentService()
    payment = await payment_service.create_payment(
        session,
        user_id=user.id,
        amount=amount,
        currency="USDT",
        description=f"{payload.tier.value} {payload.billing_cycle}",
        tier=payload.tier,
        billing_cycle=payload.billing_cycle,
    )

    return PaymentResponse(payment_id=payment.id, invoice_url=payment.invoice_url)


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


class NowPaymentsIPN(BaseModel):
    order_id: str | None = None
    payment_id: str | None = None
    payment_status: str | None = None


@router.post("/ipn")
async def nowpayments_ipn(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    settings = get_settings()
    raw_body = await request.body()
    signature = request.headers.get("x-nowpayments-sig", "")
    payload_data = json.loads(raw_body.decode())
    if not verify_nowpayments_signature(payload_data, signature, settings.nowpayments_ipn_secret):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = NowPaymentsIPN.model_validate(payload_data)
    if not payload.order_id:
        raise HTTPException(status_code=400, detail="Missing order_id")

    payment = await session.get(Payment, int(payload.order_id))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payload.payment_id and not payment.provider_payment_id:
        payment.provider_payment_id = payload.payment_id

    if payment.status == PaymentStatus.CONFIRMED:
        return {"status": "already_confirmed"}

    final_statuses = {"confirmed", "finished"}
    if (payload.payment_status or "").lower() not in final_statuses:
        return {"status": "ignored"}

    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_at = datetime.utcnow()
    await session.commit()
    await session.refresh(payment)

    months = 12 if payment.billing_cycle == "yearly" else 1
    subscription_service = SubscriptionService()
    await subscription_service.activate_for_payment(
        session,
        user_id=payment.user_id,
        tier=payment.tier,
        months=months,
    )

    return {"status": "confirmed"}
