"""
The Odds API integration — fetches real bookmaker odds to find value bets.

Sign up at https://the-odds-api.com — free tier gives 500 requests/month.
That's enough to scan odds every 30 minutes for your key markets.

Supported sports (key ones):
  americanfootball_nfl, basketball_nba, soccer_epl, baseball_mlb,
  icehockey_nhl, basketball_ncaab, americanfootball_ncaaf, mma_mixed_martial_arts,
  boxing_boxing, soccer_uefa_champs_league
"""
import httpx
from typing import Optional
from app.config import settings

ODDS_BASE = "https://api.the-odds-api.com/v4"


class OddsEvent:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.sport = data["sport_key"]
        self.home_team = data["home_team"]
        self.away_team = data["away_team"]
        self.commence_time = data["commence_time"]
        self.bookmakers = data.get("bookmakers", [])

    def best_odds_for(self, team: str) -> Optional[tuple[str, float]]:
        """Return (bookmaker_name, best_decimal_odds) for a given team."""
        best_book, best_odds = None, 0.0
        for bm in self.bookmakers:
            for market in bm.get("markets", []):
                if market["key"] != "h2h":
                    continue
                for outcome in market["outcomes"]:
                    if outcome["name"] == team and outcome["price"] > best_odds:
                        best_odds = outcome["price"]
                        best_book = bm["key"]
        return (best_book, best_odds) if best_book else None

    def all_h2h_odds(self) -> dict[str, list[tuple[str, float]]]:
        """Return {team_name: [(bookmaker, decimal_odds), ...]} for all bookmakers."""
        result: dict = {}
        for bm in self.bookmakers:
            for market in bm.get("markets", []):
                if market["key"] != "h2h":
                    continue
                for outcome in market["outcomes"]:
                    result.setdefault(outcome["name"], []).append(
                        (bm["key"], outcome["price"])
                    )
        return result


async def fetch_odds(sport: str, regions: str = "us,uk", markets: str = "h2h") -> list[OddsEvent]:
    """Fetch live odds from The Odds API."""
    if not settings.the_odds_api_key:
        return []

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{ODDS_BASE}/sports/{sport}/odds",
            params={
                "apiKey": settings.the_odds_api_key,
                "regions": regions,
                "markets": markets,
                "oddsFormat": "decimal",
            },
        )
        resp.raise_for_status()
        return [OddsEvent(e) for e in resp.json()]


async def fetch_sports() -> list[dict]:
    """List all available sports."""
    if not settings.the_odds_api_key:
        return []
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{ODDS_BASE}/sports",
            params={"apiKey": settings.the_odds_api_key},
        )
        resp.raise_for_status()
        return resp.json()


def decimal_to_implied_prob(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability (includes vig)."""
    if decimal_odds <= 0:
        return 0.0
    return 1.0 / decimal_odds


def no_vig_probability(home_odds: float, away_odds: float) -> tuple[float, float]:
    """
    Remove the bookmaker's overround to get true implied probabilities.
    Essential for fair EV comparison.
    """
    raw_home = decimal_to_implied_prob(home_odds)
    raw_away = decimal_to_implied_prob(away_odds)
    total = raw_home + raw_away
    return raw_home / total, raw_away / total


# --- Mock odds for demo (when API key not set) ---
MOCK_EVENTS = [
    {
        "id": "mock1",
        "sport_key": "basketball_nba",
        "home_team": "Los Angeles Lakers",
        "away_team": "Golden State Warriors",
        "commence_time": "2026-03-22T02:00:00Z",
        "bookmakers": [
            {"key": "draftkings", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Los Angeles Lakers", "price": 1.87},
                {"name": "Golden State Warriors", "price": 1.95},
            ]}]},
            {"key": "fanduel", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Los Angeles Lakers", "price": 1.90},
                {"name": "Golden State Warriors", "price": 1.91},
            ]}]},
            {"key": "betmgm", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Los Angeles Lakers", "price": 1.83},
                {"name": "Golden State Warriors", "price": 2.00},
            ]}]},
        ],
    },
    {
        "id": "mock2",
        "sport_key": "basketball_nba",
        "home_team": "Boston Celtics",
        "away_team": "Miami Heat",
        "commence_time": "2026-03-22T00:00:00Z",
        "bookmakers": [
            {"key": "draftkings", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Boston Celtics", "price": 1.45},
                {"name": "Miami Heat", "price": 2.75},
            ]}]},
            {"key": "fanduel", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Boston Celtics", "price": 1.48},
                {"name": "Miami Heat", "price": 2.70},
            ]}]},
        ],
    },
    {
        "id": "mock3",
        "sport_key": "americanfootball_nfl",
        "home_team": "Kansas City Chiefs",
        "away_team": "Philadelphia Eagles",
        "commence_time": "2026-03-23T18:00:00Z",
        "bookmakers": [
            {"key": "draftkings", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Kansas City Chiefs", "price": 1.65},
                {"name": "Philadelphia Eagles", "price": 2.20},
            ]}]},
            {"key": "fanduel", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Kansas City Chiefs", "price": 1.67},
                {"name": "Philadelphia Eagles", "price": 2.18},
            ]}]},
        ],
    },
]


def get_mock_events() -> list[OddsEvent]:
    return [OddsEvent(e) for e in MOCK_EVENTS]
