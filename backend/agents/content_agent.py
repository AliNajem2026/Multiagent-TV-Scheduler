import csv
from pathlib import Path

from backend.services.sports_api import (
    day_name_to_date,
    fetch_sports_events,
    fetch_tv_sports,
)


class ContentAgent:
    def run(self, day: str = None) -> list[dict]:
        if day:
            date_str = day_name_to_date(day)
            programs = fetch_sports_events(date_str)
            if not programs:
                programs = fetch_tv_sports(date_str)
        else:
            programs = []

        if not programs:
            programs = self._load_csv()

        return programs

    def _load_csv(self) -> list[dict]:
        programs = []
        csv_path = Path("data/programs.csv")
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                programs.append({
                    "title": row["title"],
                    "category": row["category"],
                    "duration": int(row["duration"]),
                })
        return programs
