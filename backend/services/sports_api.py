import os
from datetime import datetime, timedelta

import httpx


def day_name_to_date(day_name: str) -> str:
    """Map a weekday name to the nearest upcoming date as YYYY-MM-DD."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = datetime.today()
    target_weekday = days.index(day_name)
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7  # always use next occurrence, not today
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def fetch_sports_events(date_str: str, sport: str = "Soccer") -> list[dict]:
    """Fetch upcoming sports events from TheSportsDB (free public key 123)."""
    url = "https://www.thesportsdb.com/api/v1/json/123/eventsday.php"
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params={"d": date_str, "s": sport})
            resp.raise_for_status()
            events = resp.json().get("events") or []
            programs = []
            for event in events:
                programs.append({
                    "title": event.get("strEvent", "Unknown Match"),
                    "category": "Sports",
                    "duration": 90,
                    "league": event.get("strLeague", ""),
                    "scheduled_time": event.get("strTime", ""),
                })
            return programs
    except Exception:
        return []


def fetch_tv_sports(date_str: str) -> list[dict]:
    """Fallback: fetch sports TV programmes from TVMaze schedule (UK, no auth)."""
    country = os.getenv("TV_COUNTRY", "GB")
    url = "https://api.tvmaze.com/schedule"
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params={"country": country, "date": date_str})
            resp.raise_for_status()
            episodes = resp.json()
            programs = []
            for ep in episodes:
                show = ep.get("show", {})
                genres = show.get("genres", [])
                if any(g.lower() in ("sports", "sport") for g in genres):
                    programs.append({
                        "title": show.get("name", "Unknown Show"),
                        "category": "Sports",
                        "duration": ep.get("runtime") or 60,
                        "scheduled_time": ep.get("airtime", ""),
                    })
            return programs
    except Exception:
        return []
