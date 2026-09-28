"""RescueTime API client."""

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

from rescuetime_mcp.models import DailySummary, AnalyticDataRow, HourlyData


def find_env_file() -> Path:
    """Find the .env file, checking multiple locations."""
    locations = [
        Path(__file__).parent.parent.parent / ".env",
        Path.cwd() / ".env",
    ]
    for path in locations:
        if path.exists():
            return path
    return locations[0]


def _fill_from_keychain(*names):
    """Fill missing secrets from the Keychain via `secrets` (1Password holds the master copy)."""
    import subprocess
    for name in names:
        if not os.environ.get(name):
            r = subprocess.run([os.path.expanduser("~/.local/bin/secrets"), "get", name],
                               capture_output=True, text=True)
            if r.returncode == 0 and r.stdout:
                os.environ[name] = r.stdout


ENV_PATH = find_env_file()
load_dotenv(ENV_PATH)
_fill_from_keychain("RESCUETIME_API_KEY")


class RescueTimeAuthError(Exception):
    """Authentication error with RescueTime API."""

    pass


class RescueTimeAPIError(Exception):
    """General RescueTime API error."""

    pass


class RescueTimeClient:
    """Async client for RescueTime API."""

    BASE_URL = "https://www.rescuetime.com/anapi"

    def __init__(self):
        """Initialize the client with API key from environment."""
        self.api_key = os.getenv("RESCUETIME_API_KEY")

        if not self.api_key:
            raise RescueTimeAuthError(
                "No API key found. Set RESCUETIME_API_KEY in .env or environment. "
                "Get your key at: https://www.rescuetime.com/anapi/manage"
            )

    async def _request(
        self,
        endpoint: str,
        params: Optional[dict] = None,
    ) -> dict | list:
        """Make an authenticated request to the RescueTime API."""
        url = f"{self.BASE_URL}/{endpoint}"
        request_params = {"key": self.api_key, "format": "json"}
        if params:
            request_params.update(params)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=request_params)

            if response.status_code == 401:
                raise RescueTimeAuthError("Invalid API key")

            if response.status_code == 429:
                raise RescueTimeAPIError("Rate limit exceeded. Try again later.")

            if response.status_code != 200:
                raise RescueTimeAPIError(
                    f"API error {response.status_code}: {response.text}"
                )

            return response.json()

    async def get_daily_summary(self) -> list[DailySummary]:
        """Get daily summary feed (last 14 days of daily rollups).

        Returns productivity pulse, time by productivity level, and category breakdowns.
        """
        data = await self._request("daily_summary_feed")

        if not data:
            return []

        return [DailySummary.model_validate(day) for day in data]

    async def get_analytic_data(
        self,
        restrict_kind: str = "activity",
        perspective: str = "rank",
        resolution_time: str = "day",
        restrict_begin: Optional[str] = None,
        restrict_end: Optional[str] = None,
        interval: Optional[str] = None,
    ) -> list[AnalyticDataRow]:
        """Get analytic data from the main data API.

        Args:
            restrict_kind: Type of data - 'activity', 'category', 'productivity', 'document'
            perspective: 'rank' for ranked list, 'interval' for time-based
            resolution_time: 'month', 'week', 'day', 'hour', 'minute'
            restrict_begin: Start date (YYYY-MM-DD), defaults to today
            restrict_end: End date (YYYY-MM-DD), defaults to today
            interval: For interval perspective - 'hour', 'minute'
        """
        today = date.today().isoformat()
        params = {
            "perspective": perspective,
            "resolution_time": resolution_time,
            "restrict_kind": restrict_kind,
            "restrict_begin": restrict_begin or today,
            "restrict_end": restrict_end or today,
        }

        if interval and perspective == "interval":
            params["interval"] = interval

        data = await self._request("data", params)

        if not data or "rows" not in data:
            return []

        rows = []
        for row in data["rows"]:
            rows.append(
                AnalyticDataRow(
                    rank=row[0],
                    time_seconds=row[1],
                    name=row[3],
                    category=row[4] if len(row) > 4 and row[4] else None,
                    productivity=row[5] if len(row) > 5 else 0,
                )
            )

        return rows

    async def get_hourly_data(
        self,
        restrict_begin: Optional[str] = None,
        restrict_end: Optional[str] = None,
    ) -> list[HourlyData]:
        """Get hourly productivity breakdown.

        Args:
            restrict_begin: Start date (YYYY-MM-DD), defaults to today
            restrict_end: End date (YYYY-MM-DD), defaults to today
        """
        today = date.today().isoformat()
        params = {
            "perspective": "interval",
            "resolution_time": "hour",
            "restrict_kind": "productivity",
            "restrict_begin": restrict_begin or today,
            "restrict_end": restrict_end or today,
        }

        data = await self._request("data", params)

        if not data or "rows" not in data:
            return []

        hourly = []
        for row in data["rows"]:
            # Row format for interval: [date, time_seconds, num_people, productivity]
            # Date is like "2024-01-15T14:00:00"
            date_str = row[0]
            hour = int(date_str.split("T")[1].split(":")[0])
            date_part = date_str.split("T")[0]

            hourly.append(
                HourlyData(
                    hour=hour,
                    date=date_part,
                    time_seconds=row[1],
                    productivity=row[3] if len(row) > 3 else 0,
                )
            )

        return hourly
