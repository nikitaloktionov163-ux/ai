# Cryptum Prime

Production-ready foundation for a Telegram bot + FastAPI backend that delivers AI-based crypto chart analysis, market insights, and education with paid subscriptions (PRO / PRIME). **No trading execution and no financial advice.**

## Features (MVP-ready)
- Telegram bot with language selection, main menu, exchange selection, chart analysis flow, subscription menu, education mode, and FAQ.
- FastAPI backend for user management, subscriptions, payments, and AI analysis.
- OpenAI Vision + Text integration for chart analysis.
- PostgreSQL (prod) / SQLite (dev) support via SQLAlchemy.
- Redis-backed rate limiting and abuse prevention hooks.
- USDT payment flow scaffold (manual confirmation + webhook-ready providers).
- Admin commands for managing users and subscriptions.
- Clean, modular architecture for easy extension.

## Architecture
```
cryptum_prime/
  app/                # FastAPI backend
  bot/                # Telegram bot
  docs/               # docs and diagrams (optional)
  .env.example
  requirements.txt
```

## Setup

### 1) Create virtualenv & install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment
Copy `.env.example` to `.env` and fill in values.

### 3) Initialize database
```bash
python -m app.db.init_db
```

### 4) Run FastAPI
```bash
uvicorn app.main:app --reload
```

### 5) Run Telegram bot
```bash
python -m bot.main
```

## Notes
- Payment providers are abstracted. To go live, implement a provider (CoinPayments/NOWPayments/Binance Pay) in `app/payments/providers.py`.
- Rate limiting uses Redis. Ensure Redis is running and `REDIS_URL` is configured.
- The AI analysis endpoint expects an image and a `<PAIR> <TIMEFRAME>` message.

## Disclaimer
Cryptum Prime does **not** execute trades. All outputs are educational and informational only, not financial advice.
