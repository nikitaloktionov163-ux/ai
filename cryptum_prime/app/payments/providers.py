from dataclasses import dataclass
from typing import Protocol

from app.core.config import get_settings


@dataclass
class PaymentRequest:
    amount: float
    currency: str
    description: str


@dataclass
class PaymentResponse:
    address: str
    network: str
    provider_reference: str


class PaymentProvider(Protocol):
    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        ...


class ManualUSDTProvider:
    def __init__(self) -> None:
        settings = get_settings()
        self.wallet_address = settings.usdt_wallet_address
        self.network = settings.usdt_network

    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        return PaymentResponse(
            address=self.wallet_address,
            network=self.network,
            provider_reference="manual",
        )


def get_provider() -> PaymentProvider:
    settings = get_settings()
    if settings.payment_provider == "manual":
        return ManualUSDTProvider()
    return ManualUSDTProvider()
