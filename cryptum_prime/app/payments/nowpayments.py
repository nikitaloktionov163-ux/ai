from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class NowPaymentsInvoice:
    payment_id: str
    invoice_url: str | None
    pay_address: str | None
    pay_currency: str | None


class NowPaymentsClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.nowpayments_api_key
        self.base_url = "https://api.nowpayments.io/v1"

    async def create_invoice(
        self,
        amount: float,
        price_currency: str,
        pay_currency: str,
        order_id: str,
        description: str,
        ipn_callback_url: str,
    ) -> NowPaymentsInvoice:
        payload = {
            "price_amount": amount,
            "price_currency": price_currency,
            "pay_currency": pay_currency,
            "order_id": order_id,
            "order_description": description,
            "ipn_callback_url": ipn_callback_url,
        }
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self.base_url}/payment",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return NowPaymentsInvoice(
            payment_id=str(data.get("payment_id", "")),
            invoice_url=data.get("invoice_url"),
            pay_address=data.get("pay_address"),
            pay_currency=data.get("pay_currency"),
        )


def verify_nowpayments_signature(payload: dict, signature: str, secret: str) -> bool:
    if not signature or not secret:
        return False
    message = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    digest = hmac.new(secret.encode(), message.encode(), hashlib.sha512).hexdigest()
    return hmac.compare_digest(digest, signature)


def serialize_nowpayments_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
