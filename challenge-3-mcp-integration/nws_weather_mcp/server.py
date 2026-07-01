import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nws_weather_mcp")

NWS_BASE_URL = "https://api.weather.gov"
USER_AGENT = os.getenv(
    "NWS_USER_AGENT",
    "challenge-3-mcp-integration/1.0 (contact: student@example.com)",
)


def _get_json(url: str) -> dict[str, Any]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }
    with httpx.Client(timeout=20.0, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def _point_metadata(latitude: float, longitude: float) -> dict[str, Any]:
    points_url = f"{NWS_BASE_URL}/points/{latitude},{longitude}"
    return _get_json(points_url)


@mcp.tool()
def forecast_by_point(latitude: float, longitude: float) -> dict[str, Any]:
    """Get a short daily forecast from NWS for a latitude/longitude pair in the US.

    Args:
        latitude: Decimal latitude (e.g., 47.6062).
        longitude: Decimal longitude (e.g., -122.3321).

    Returns:
        Structured forecast summary and periods.
    """
    point_data = _point_metadata(latitude, longitude)
    properties = point_data.get("properties", {})
    forecast_url = properties.get("forecast")
    if not forecast_url:
        raise ValueError("NWS forecast URL not available for this location.")

    forecast_data = _get_json(forecast_url)
    forecast_props = forecast_data.get("properties", {})
    periods = forecast_props.get("periods", [])[:6]

    relative_location = properties.get("relativeLocation", {}).get("properties", {})

    return {
        "source": "National Weather Service (api.weather.gov)",
        "location": {
            "city": relative_location.get("city"),
            "state": relative_location.get("state"),
            "lat": latitude,
            "lon": longitude,
        },
        "updated": forecast_props.get("updated"),
        "periods": [
            {
                "name": p.get("name"),
                "temperature": p.get("temperature"),
                "temperatureUnit": p.get("temperatureUnit"),
                "windSpeed": p.get("windSpeed"),
                "windDirection": p.get("windDirection"),
                "shortForecast": p.get("shortForecast"),
                "detailedForecast": p.get("detailedForecast"),
            }
            for p in periods
        ],
    }


@mcp.tool()
def hourly_forecast_by_point(latitude: float, longitude: float) -> dict[str, Any]:
    """Get the next hourly forecast periods from NWS for a latitude/longitude pair in the US.

    Args:
        latitude: Decimal latitude (e.g., 47.6062).
        longitude: Decimal longitude (e.g., -122.3321).

    Returns:
        Structured hourly forecast periods.
    """
    point_data = _point_metadata(latitude, longitude)
    properties = point_data.get("properties", {})
    forecast_hourly_url = properties.get("forecastHourly")
    if not forecast_hourly_url:
        raise ValueError("NWS hourly forecast URL not available for this location.")

    forecast_data = _get_json(forecast_hourly_url)
    forecast_props = forecast_data.get("properties", {})
    periods = forecast_props.get("periods", [])[:12]

    relative_location = properties.get("relativeLocation", {}).get("properties", {})

    return {
        "source": "National Weather Service (api.weather.gov)",
        "location": {
            "city": relative_location.get("city"),
            "state": relative_location.get("state"),
            "lat": latitude,
            "lon": longitude,
        },
        "updated": forecast_props.get("updated"),
        "periods": [
            {
                "startTime": p.get("startTime"),
                "temperature": p.get("temperature"),
                "temperatureUnit": p.get("temperatureUnit"),
                "windSpeed": p.get("windSpeed"),
                "windDirection": p.get("windDirection"),
                "shortForecast": p.get("shortForecast"),
            }
            for p in periods
        ],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
