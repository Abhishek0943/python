"""Project 5: Weather CLI (Open-Meteo, no API key needed)

Setup (once):
    python -m venv venv
    source venv/bin/activate        # Windows: venv\\Scripts\\activate
    pip install requests

Run:
    python weather.py Chandigarh
    python weather.py "New York" --days 3
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_FILE = Path("weather_cache.json")
CACHE_SECONDS = 10 * 60  # reuse a result for 10 minutes

# Open-Meteo returns a numeric "weather code"; this maps the common ones to text
WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm",
}


def describe(code):
    return WEATHER_CODES.get(code, f"Unknown (code {code})")


# ---------- cache ----------
def load_cache():
    try:
        return json.loads(CACHE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


# ---------- API calls ----------
def get_json(url, params):
    """GET a URL and return the parsed JSON, raising on HTTP errors."""
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()  # turns 4xx/5xx into an exception
    return response.json()


def find_city(name):
    """Step 1: city name -> (display name, latitude, longitude)."""
    data = get_json(GEOCODE_URL, {"name": name, "count": 1})
    results = data.get("results")  # key is missing when nothing matches
    if not results:
        return None
    place = results[0]
    label = f"{place['name']}, {place.get('country', '')}".strip(", ")
    return label, place["latitude"], place["longitude"]


def get_forecast(lat, lon, days):
    """Step 2: coordinates -> current weather + daily forecast."""
    return get_json(FORECAST_URL, {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "forecast_days": days,
        "timezone": "auto",
    })


# ---------- output ----------
def show(label, data, days):
    current = data["current"]
    print(f"\nWeather in {label}")
    print(f"  Now:  {current['temperature_2m']}°C, {describe(current['weather_code'])}")
    print(f"  Wind: {current['wind_speed_10m']} km/h")

    if days > 1:
        daily = data["daily"]
        print(f"\n{days}-day forecast:")
        # zip walks the parallel lists together, like an index loop
        for day, low, high, code in zip(daily["time"], daily["temperature_2m_min"],
                                        daily["temperature_2m_max"], daily["weather_code"]):
            print(f"  {day}  {low:>5}°C – {high:>5}°C  {describe(code)}")


def parse_args():
    parser = argparse.ArgumentParser(description="Show the weather for a city.")
    parser.add_argument("city", help='city name, e.g. Chandigarh or "New York"')
    parser.add_argument("--days", type=int, default=1, choices=range(1, 8),
                        metavar="1-7", help="number of forecast days (default 1)")
    return parser.parse_args()


def main():
    args = parse_args()
    key = f"{args.city.lower()}|{args.days}"
    cache = load_cache()

    entry = cache.get(key)
    if entry and time.time() - entry["saved_at"] < CACHE_SECONDS:
        show(entry["label"], entry["data"], args.days)
        print("\n(cached result)")
        return

    try:
        place = find_city(args.city)
        if place is None:
            sys.exit(f"City '{args.city}' not found.")
        label, lat, lon = place
        data = get_forecast(lat, lon, args.days)
    except requests.exceptions.Timeout:
        sys.exit("The weather service took too long to respond. Try again.")
    except requests.exceptions.ConnectionError:
        sys.exit("Could not connect. Check your internet connection.")
    except requests.exceptions.RequestException as e:
        sys.exit(f"Request failed: {e}")

    cache[key] = {"saved_at": time.time(), "label": label, "data": data}
    save_cache(cache)
    show(label, data, args.days)


if __name__ == "__main__":
    main()
