import os
import smtplib
import ssl
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv


LOCATION_NAME = "Statesboro GA"
LATITUDE = 32.4488
LONGITUDE = -81.7832
TIMEZONE = "America/New_York"
SMS_GATEWAY = "6059639101@tmomail.net"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def weather_code_to_summary(code: int) -> str:
    code_map = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Dense drizzle",
        56: "Freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        66: "Freezing rain",
        67: "Heavy freezing rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Rain showers",
        81: "Showers",
        82: "Heavy showers",
        85: "Snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm hail",
        99: "Severe thunderstorm",
    }
    return code_map.get(code, "Weather update")


def get_target_date(timezone: str, days_ahead: int = 1) -> str:
    now = datetime.now(ZoneInfo(timezone))
    target = now + timedelta(days=days_ahead)
    return target.date().isoformat()


def get_forecast(days_ahead: int = 1) -> dict:
    target_date = get_target_date(TIMEZONE, days_ahead=days_ahead)
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
        "temperature_unit": "fahrenheit",
        "timezone": TIMEZONE,
        "forecast_days": max(3, days_ahead + 2),
    }

    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"Weather API request failed: {exc}") from exc

    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    rain_probs = daily.get("precipitation_probability_max", [])
    weather_codes = daily.get("weathercode", [])

    try:
        idx = dates.index(target_date)
    except ValueError as exc:
        raise RuntimeError(f"Target date ({target_date}) not found in forecast data.") from exc

    return {
        "date_iso": dates[idx],
        "high_f": round(highs[idx]),
        "low_f": round(lows[idx]),
        "rain_chance": round(rain_probs[idx]),
        "summary": weather_code_to_summary(int(weather_codes[idx])),
    }


def format_sms_message(forecast: dict, force_single_line: bool = False) -> str:
    date_obj = datetime.strptime(forecast["date_iso"], "%Y-%m-%d")
    date_str = date_obj.strftime("%b %d")
    max_len = 160

    # Option 1: compact multiline (preferred for readability).
    line1 = f"{date_str} Weather"
    line2 = LOCATION_NAME
    line3 = f"High {forecast['high_f']}F Low {forecast['low_f']}F"
    line4 = f"Rain {forecast['rain_chance']}%"
    multiline = f"{line1}\n{line2}\n{line3}\n{line4}\n{forecast['summary']}"
    if not force_single_line and len(multiline) <= max_len:
        return multiline

    # Option 3: single-line summary fallback for strict SMS length safety.
    single_line = (
        f"{date_str} {LOCATION_NAME} "
        f"High {forecast['high_f']}F Low {forecast['low_f']}F "
        f"Rain {forecast['rain_chance']}% {forecast['summary']}"
    )
    return single_line[:max_len]


def send_sms_via_email(gmail_user: str, gmail_app_password: str, message: str) -> None:
    subject = ""
    body = message
    email_message = f"Subject: {subject}\n\n{body}"

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, SMS_GATEWAY, email_message.encode("utf-8"))
    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            "SMTP auth failed. Use a Gmail App Password in GMAIL_APP_PASSWORD "
            "(16 characters, no spaces), and make sure 2-Step Verification is enabled."
        ) from exc
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"SMTP send failed: {exc}") from exc


def parse_days_ahead(argv: list[str]) -> int:
    if len(argv) < 2:
        return 1
    raw_value = argv[1].strip()
    try:
        days_ahead = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("Invalid days_ahead argument. Use an integer like 1.") from exc
    if days_ahead < 0:
        raise RuntimeError("days_ahead must be 0 or greater.")
    return days_ahead


def main() -> int:
    load_dotenv()
    gmail_user = os.getenv("GMAIL_USER", "").strip()
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()

    if not gmail_user or not gmail_app_password:
        print("ERROR: Missing GMAIL_USER or GMAIL_APP_PASSWORD in environment.")
        return 1

    force_single_line = os.getenv("FORCE_SINGLE_LINE", "").strip().lower() in {"1", "true", "yes"}

    try:
        days_ahead = parse_days_ahead(sys.argv)
        forecast = get_forecast(days_ahead=days_ahead)
        print(f"Preparing T+{days_ahead} forecast for {forecast['date_iso']} ({LOCATION_NAME})")
        if force_single_line:
            print("FORCE_SINGLE_LINE enabled: using single-line SMS format.")
        sms_message = format_sms_message(forecast, force_single_line=force_single_line)
        print(f"SMS length: {len(sms_message)} characters")
        send_sms_via_email(gmail_user, gmail_app_password, sms_message)
        print("Success: Forecast SMS sent.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
