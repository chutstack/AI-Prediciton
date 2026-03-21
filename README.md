# AI Prediction Platform — Make Money Through Your Picks

A full-stack platform for finding +EV betting opportunities, tracking picks with verified P&L, and monetizing your edge through paid communities.

---

## The Money-Making Strategy

There are 3 stacked ways to profit from this platform:

### 1. Value Betting (Your Own Capital)
Find bets where your model's confidence is higher than the bookmaker's implied probability — that's +EV. Bet these consistently and you profit over the long run.

**Math:** If your model says 60% and the odds imply 50%, your edge is +10%. Kelly Criterion tells you how much of your bankroll to bet.

**Reality:** Target 5-10% ROI. At $1,000 bankroll and 5 bets/day at $20 avg stake → ~$100/month. Scale the bankroll, scale the returns. Professional bettors target 4-10% ROI.

### 2. Sell Picks (Most Reliable Income)
Once you have 50+ picks with positive ROI, list your picks service on **Whop.com** or a paid Telegram channel. You get paid regardless of outcomes — subscribers pay for the signal, not the outcome.

**Pricing:** $29–$99/month per subscriber. At 50 subscribers × $49 = **$2,450/month**.

**Growth path:**
- Build public track record first (this platform tracks it for you)
- Post free picks on Twitter/X to attract followers
- Convert followers → paid subscribers via Whop or Telegram

### 3. Prediction Markets (No Account Bans)
Sportsbooks ban winning bettors. Prediction markets (Polymarket, Kalshi) don't — they welcome sophisticated traders. Use your model there for crypto/sports/politics markets.

---

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Add THE_ODDS_API_KEY for live bookmaker odds (free at the-odds-api.com)
# Add TELEGRAM_BOT_TOKEN + TELEGRAM_CHANNEL_ID to publish picks

# 3. Run
uvicorn app.main:app --reload

# 4. Open http://localhost:8000
```

---

## Core Workflow

```
1. Open dashboard → "Value Scanner"
2. Select sport → Scan Now
   → AI model runs against live bookmaker odds
   → Shows EV% for each matchup
3. Click "Log This Pick" on any +EV bet
   → Timestamped before event (builds verified record)
   → Kelly-optimal stake calculated automatically
4. Click "Publish" → sends pick to Telegram channel
5. After event: click "Record Result"
   → P&L calculated, track record updated
6. Dashboard → "Track Record" shows your verified stats
   → When 50+ picks + 5%+ ROI → ready to list on Whop
```

---

## Architecture

```
AI-Prediciton/
├── app/
│   ├── main.py                     # FastAPI app
│   ├── config.py                   # Env settings
│   ├── database.py                 # SQLAlchemy
│   ├── models/
│   │   ├── user.py                 # Auth + subscription state
│   │   ├── pick.py                 # ⭐ Pick record with P&L, EV, Kelly
│   │   ├── prediction.py           # Raw model outputs
│   │   └── transaction.py          # Billing history
│   ├── routes/
│   │   ├── auth.py                 # Register / login / JWT
│   │   ├── picks.py                # ⭐ Value scanner, Kelly calc, pick CRUD
│   │   ├── predictions.py          # Raw prediction generation
│   │   └── billing.py              # Subscription management
│   └── services/
│       ├── prediction_engine.py    # ML models (Sports, Crypto, Stocks)
│       ├── odds_service.py         # ⭐ The Odds API — live bookmaker odds
│       ├── value_calculator.py     # ⭐ EV%, Kelly criterion, P&L analysis
│       └── telegram_publisher.py   # ⭐ Push picks to Telegram channel
├── frontend/
│   ├── templates/
│   │   ├── index.html              # Landing page
│   │   ├── dashboard.html          # ⭐ Value scanner + pick tracker
│   │   └── pricing.html            # Subscription tiers
│   └── static/
│       ├── css/styles.css
│       └── js/api.js
└── tests/
    └── test_monetization.py
```

---

## API Reference

Full docs at **http://localhost:8000/docs**

### Key Endpoints

| Method | Endpoint | What it does |
|--------|----------|-------------|
| GET | `/picks/scan-value?sport=basketball_nba&min_ev=3` | Run model vs. live odds, find +EV bets |
| POST | `/picks/kelly` | Calculate Kelly-optimal bet size |
| POST | `/picks` | Log a pick (timestamped) |
| PATCH | `/picks/{id}/result` | Record win/loss, compute P&L |
| POST | `/picks/{id}/publish` | Send to Telegram channel |
| GET | `/picks/record` | Public verified track record |

---

## Setting Up The Odds API

1. Sign up at [the-odds-api.com](https://the-odds-api.com) — free tier = 500 requests/month
2. Set `THE_ODDS_API_KEY=your_key` in `.env`
3. That's it — the scanner uses live odds automatically

Free tier scan strategy: scan once every 4 hours = ~180 requests/month, leaves 320 for other queries.

## Setting Up Telegram Publishing

1. Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the token
2. Create a channel, add your bot as admin
3. Set in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=7123456789:AAHxxx
   TELEGRAM_CHANNEL_ID=@yourchannel
   ```
4. Use "Log + Publish" when logging picks, or "Publish" on any existing pick

**Free vs Paid channel strategy:**
- Free channel: post picks without exact odds/confidence (teaser)
- Paid channel: full details — confidence %, EV%, Kelly stake, bookmaker

## Listing on Whop.com

1. Build 50+ resolved picks with 5%+ ROI
2. Sign up at [whop.com](https://whop.com/sell)
3. Create a product linked to your Telegram/Discord
4. Whop handles payments, access, and churn automatically
5. Suggested pricing: $29/mo basic, $69/mo premium (with analysis)

---

## Replacing Mock Models With Real Data

The prediction engine uses simulated signals by default. For real edge, connect real data:

| Market | Recommended Data Sources |
|--------|--------------------------|
| Sports | The Odds API (for odds + line movement), Sportradar |
| Crypto | Binance WebSocket, CoinGecko, Glassnode |
| Stocks | Polygon.io, Alpaca Markets |
| Prediction Markets | Polymarket API, Kalshi API |
