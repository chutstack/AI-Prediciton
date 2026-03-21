# AI Prediction Platform

A complete, monetizable AI prediction platform for sports, crypto, and stock markets.

## Monetization Model

| Tier | Price | Predictions/Month | Markets | Premium Signals |
|------|-------|-------------------|---------|-----------------|
| **Free** | $0 | 5 | Sports | ✗ |
| **Basic** | $9.99/mo | 50 | Sports + Crypto | Credits only |
| **Pro** | $29.99/mo | 500 | All (Sports, Crypto, Stocks, Forex) | ✓ Included |
| **Enterprise** | $99.99/mo | Unlimited | All + Custom | ✓ + API Access |

**Credit Packs** (pay-per-prediction for non-subscribers):
- Starter: 25 credits / $5
- Standard: 75 credits / $12 (20% bonus)
- Pro Pack: 200 credits / $25 (60% bonus)

Each premium signal costs 1 credit (~$0.20). Premium = confidence >80%.

### Revenue Projections
At 1,000 users with typical SaaS conversion rates (60% free, 25% Basic, 12% Pro, 3% Enterprise):
- Basic: 250 × $9.99 = **$2,497/mo**
- Pro: 120 × $29.99 = **$3,599/mo**
- Enterprise: 30 × $99.99 = **$2,999/mo**
- Credits: ~**$1,000/mo**
- **MRR: ~$10,095**

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env — add your Stripe keys for live payments

# 3. Run the server
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 — the landing page, dashboard, and pricing are live.

---

## Architecture

```
AI-Prediciton/
├── app/
│   ├── main.py                   # FastAPI app + lifespan/startup
│   ├── config.py                 # Settings via .env
│   ├── database.py               # SQLAlchemy setup
│   ├── models/
│   │   ├── user.py               # User + SubscriptionTier + TIER_LIMITS
│   │   ├── prediction.py         # Prediction records
│   │   └── transaction.py        # Billing/payment transactions
│   ├── routes/
│   │   ├── auth.py               # Register, login, /me
│   │   ├── predictions.py        # Generate, history, stats
│   │   └── billing.py            # Subscriptions, credits, Stripe webhook
│   └── services/
│       ├── auth.py               # JWT, password hashing
│       ├── prediction_engine.py  # ML prediction models (Sports, Crypto, Stocks)
│       └── monetization.py       # Quota enforcement, credit deduction, revenue
├── frontend/
│   ├── templates/
│   │   ├── index.html            # Landing page with public signal teaser
│   │   ├── dashboard.html        # User dashboard
│   │   └── pricing.html          # Pricing + credit packs
│   └── static/
│       ├── css/styles.css
│       └── js/api.js             # Frontend API client
└── tests/
    └── test_monetization.py
```

---

## API Reference

All endpoints documented at **http://localhost:8000/docs** (Swagger UI).

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/token` | Login → JWT token |
| GET | `/auth/me` | Get current user |

### Predictions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predictions/public` | Free teaser signals (no auth) |
| POST | `/predictions/generate` | Generate AI prediction |
| GET | `/predictions/history` | User's prediction history |
| GET | `/predictions/stats` | Win rate + quota usage |

### Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/billing/plans` | All plans + credit packs |
| POST | `/billing/subscribe` | Create Stripe Checkout session |
| POST | `/billing/buy-credits` | Purchase credit pack |
| POST | `/billing/demo-activate` | **Dev only** — activate without payment |
| POST | `/billing/cancel` | Cancel subscription |
| POST | `/billing/webhook` | Stripe webhook handler |
| GET | `/billing/revenue` | Platform revenue metrics |
| GET | `/billing/transactions` | User billing history |

---

## Setting Up Stripe (Live Payments)

1. Create account at [stripe.com](https://stripe.com)
2. Create 3 subscription products in Stripe Dashboard:
   - Basic Plan: $9.99/month → copy Price ID
   - Pro Plan: $29.99/month → copy Price ID
   - Enterprise Plan: $99.99/month → copy Price ID
3. Set in `.env`:
   ```
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_BASIC_PRICE_ID=price_...
   STRIPE_PRO_PRICE_ID=price_...
   STRIPE_ENTERPRISE_PRICE_ID=price_...
   ```
4. Point Stripe webhook to `https://yourdomain.com/billing/webhook`
5. Remove the `/billing/demo-activate` endpoint before going live

---

## Replacing Mock Models with Real Data

The prediction engine (`app/services/prediction_engine.py`) currently uses simulated feature data.
Replace the data fetchers with real API calls:

| Market | Recommended APIs |
|--------|-----------------|
| Sports | The Odds API, Sportradar, Pinnacle |
| Crypto | Binance WebSocket, CoinGecko, Messari |
| Stocks | Alpaca Markets, Polygon.io, Yahoo Finance |
| Forex | OANDA, Alpha Vantage |

---

## Growth Levers

1. **SEO / Content**: Post daily prediction summaries → organic traffic
2. **Track record page**: Public win-rate leaderboard builds trust
3. **Referral program**: Give 5 free credits per referred signup
4. **Affiliate partnerships**: Revenue share with sportsbooks/exchanges
5. **White-label API**: Sell prediction feeds to other apps (Enterprise)
6. **Discord/Telegram bot**: Push premium signals to channels — drives upgrades
