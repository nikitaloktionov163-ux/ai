from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import httpx


@dataclass
class CachePayload:
    updated_at: datetime
    symbols: set[str]


class MarketDataService:
    _top500_cache: CachePayload | None = None
    _exchange_cache: CachePayload | None = None

    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parents[1]
        self.data_dir = base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.top500_file = self.data_dir / "top500.json"
        self.exchange_file = self.data_dir / "binance_symbols.json"
        self.top500_ttl = timedelta(hours=12)
        self.exchange_ttl = timedelta(hours=6)

    async def get_top500_symbols(self) -> set[str]:
        if self._top500_cache and not self._is_expired(self._top500_cache.updated_at, self.top500_ttl):
            return self._top500_cache.symbols

        cached = self._load_cache(self.top500_file)
        if cached and not self._is_expired(cached.updated_at, self.top500_ttl):
            self._top500_cache = cached
            return cached.symbols

        symbols = await self._fetch_top500_symbols()
        payload = CachePayload(updated_at=datetime.utcnow(), symbols=symbols)
        self._top500_cache = payload
        self._save_cache(self.top500_file, payload)
        return symbols

    async def get_exchange_symbols(self) -> set[str]:
        if self._exchange_cache and not self._is_expired(self._exchange_cache.updated_at, self.exchange_ttl):
            return self._exchange_cache.symbols

        cached = self._load_cache(self.exchange_file)
        if cached and not self._is_expired(cached.updated_at, self.exchange_ttl):
            self._exchange_cache = cached
            return cached.symbols

        symbols = await self._fetch_exchange_symbols()
        payload = CachePayload(updated_at=datetime.utcnow(), symbols=symbols)
        self._exchange_cache = payload
        self._save_cache(self.exchange_file, payload)
        return symbols

    @staticmethod
    def _is_expired(updated_at: datetime, ttl: timedelta) -> bool:
        return datetime.utcnow() - updated_at > ttl

    @staticmethod
    def _load_cache(path: Path) -> CachePayload | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            updated_at = datetime.fromisoformat(data.get("updated_at", ""))
            symbols = set(data.get("symbols", []))
            if updated_at and symbols:
                return CachePayload(updated_at=updated_at, symbols=symbols)
        except (ValueError, OSError):
            return None
        return None

    @staticmethod
    def _save_cache(path: Path, payload: CachePayload) -> None:
        data = {
            "updated_at": payload.updated_at.isoformat(),
            "symbols": sorted(payload.symbols),
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def _fetch_top500_symbols(self) -> set[str]:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        symbols: set[str] = set()
        async with httpx.AsyncClient(timeout=20.0) as client:
            for page in (1, 2):
                response = await client.get(
                    url,
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": 250,
                        "page": page,
                        "sparkline": "false",
                    },
                )
                response.raise_for_status()
                data = response.json()
                for entry in data:
                    symbol = str(entry.get("symbol", "")).upper()
                    if symbol:
                        symbols.add(symbol)
        if not symbols:
            raise RuntimeError("CoinGecko returned empty symbol set.")
        return symbols

    async def _fetch_exchange_symbols(self) -> set[str]:
        url = "https://api.binance.com/api/v3/exchangeInfo"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        symbols: set[str] = set()
        for entry in data.get("symbols", []):
            if entry.get("status") == "TRADING":
                symbol = entry.get("symbol")
                if symbol:
                    symbols.add(symbol.upper())
        if not symbols:
            raise RuntimeError("Binance returned empty symbol set.")
        return symbols
