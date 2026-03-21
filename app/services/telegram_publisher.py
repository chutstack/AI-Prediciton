"""
Telegram Bot Publisher

Sends picks to your Telegram channel automatically.

Setup:
  1. Create a bot via @BotFather on Telegram → get TELEGRAM_BOT_TOKEN
  2. Add bot to your channel as admin
  3. Get channel ID:
     - Public channel: use "@yourchannel"
     - Private channel: use numeric ID like "-1001234567890"
       (forward a message to @userinfobot to get it)
  4. Set in .env:
       TELEGRAM_BOT_TOKEN=7123456789:AAHxxx
       TELEGRAM_CHANNEL_ID=@yourchannel

Monetization path:
  - Free channel: picks without exact odds/stake (teaser)
  - Paid channel (via Whop.com): full pick details + model confidence + Kelly stake
"""
import httpx
from datetime import datetime
from typing import Optional

from app.config import settings


TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def format_pick_message(pick, full_detail: bool = True) -> str:
    """Format a pick as a Telegram message."""
    result_emoji = {
        "pending": "🔵",
        "win": "✅",
        "loss": "❌",
        "push": "↩️",
        "void": "🚫",
    }.get(pick.result.value if hasattr(pick.result, "value") else pick.result, "🔵")

    ev_emoji = "🔥" if pick.ev_percent >= 8 else "✨" if pick.ev_percent >= 3 else "⚠️"

    if full_detail:
        msg = f"""
{result_emoji} *NEW PICK* {ev_emoji}

📋 *{pick.event_name}*
🎯 **{pick.pick_label}**

📊 Model Confidence: `{round(pick.model_confidence * 100, 1)}%`
💰 Odds: `{pick.decimal_odds}` @ {pick.bookmaker or 'best available'}
📈 Expected Value: `+{pick.ev_percent}%`
🏦 Suggested Stake: `{pick.suggested_stake_pct or '—'}% of bankroll` _(Quarter Kelly)_
""".strip()
    else:
        # Free teaser — hide key details
        msg = f"""
🔵 *NEW PICK ALERT*

📋 *{pick.event_name}*
🎯 Pick revealed to paid members

🔒 Join our premium channel to get:
  • Full pick details
  • Model confidence scores
  • Kelly-optimal stake sizing
  • Live odds line shopping
""".strip()

    if pick.analysis:
        msg += f"\n\n📝 *Analysis:*\n_{pick.analysis}_"

    msg += f"\n\n_Posted {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC_"
    return msg


async def publish_to_telegram(pick, full_detail: bool = True) -> dict:
    """
    Send pick to Telegram channel.
    Returns {success, message_id} or {success: False, error}.
    """
    if not settings.telegram_bot_token or not settings.telegram_channel_id:
        return {
            "success": False,
            "error": "Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID in .env",
            "preview": format_pick_message(pick, full_detail),
        }

    message = format_pick_message(pick, full_detail)
    url = TELEGRAM_API.format(token=settings.telegram_bot_token, method="sendMessage")

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json={
            "chat_id": settings.telegram_channel_id,
            "text": message,
            "parse_mode": "Markdown",
        })
        data = resp.json()

    if data.get("ok"):
        return {
            "success": True,
            "message_id": data["result"]["message_id"],
            "preview": message,
        }
    return {
        "success": False,
        "error": data.get("description", "Unknown Telegram error"),
        "preview": message,
    }


async def send_result_update(pick) -> dict:
    """Send win/loss update when a pick resolves."""
    if not settings.telegram_bot_token or not settings.telegram_channel_id:
        return {"success": False, "error": "Telegram not configured"}

    result_emoji = "✅ WIN" if pick.result.value == "win" else "❌ LOSS"
    pnl_str = f"+${pick.profit_loss:.2f}" if pick.profit_loss and pick.profit_loss > 0 else f"-${abs(pick.profit_loss):.2f}" if pick.profit_loss else "N/A"

    msg = f"""
{result_emoji} *RESULT UPDATE*

📋 *{pick.event_name}*
🎯 {pick.pick_label}
💵 P&L: `{pnl_str}`
📊 Odds were: `{pick.decimal_odds}`

_Track record updated._
""".strip()

    url = TELEGRAM_API.format(token=settings.telegram_bot_token, method="sendMessage")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json={
            "chat_id": settings.telegram_channel_id,
            "text": msg,
            "parse_mode": "Markdown",
        })
    data = resp.json()
    return {"success": data.get("ok", False)}
