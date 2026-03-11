import os
import smtplib
import ssl
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


def get_tomorrow_date(timezone: str) -> str:
    now = datetime.now(ZoneInfo(timezone))
    tomorrow = now + timedelta(days=1)
    return tomorrow.date().isoformat()


def get_tomorrow_forecast() -> dict:
    tomorrow_date = get_tomorrow_date(TIMEZONE)
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
        "temperature_unit": "fahrenheit",
        "timezone": TIMEZONE,
        "forecast_days": 3,
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
        idx = dates.index(tomorrow_date)
    except ValueError as exc:
        raise RuntimeError(f"Tomorrow ({tomorrow_date}) not found in forecast data.") from exc

    return {
        "date_iso": dates[idx],
        "high_f": round(highs[idx]),
        "low_f": round(lows[idx]),
        "rain_chance": round(rain_probs[idx]),
        "summary": weather_code_to_summary(int(weather_codes[idx])),
    }


def format_sms_message(forecast: dict) -> str:
    date_obj = datetime.strptime(forecast["date_iso"], "%Y-%m-%d")
    date_str = date_obj.strftime("%b %d")

    line1 = f"{date_str} Weather"
    line2 = LOCATION_NAME
    line3 = f"High {forecast['high_f']}F Low {forecast['low_f']}F"
    line4 = f"Rain {forecast['rain_chance']}%"
    base = f"{line1}\n{line2}\n{line3}\n{line4}\n"

    max_len = 160
    remaining = max_len - len(base)
    summary = forecast["summary"][: max(0, remaining)]
    message = base + summary

    # Hard cap to guarantee SMS-sized output.
    return message[:max_len]


def send_sms_via_email(gmail_user: str, gmail_app_password: str, message: str) -> None:
    subject = ""
    body = message
    email_message = f"Subject: {subject}\n\n{body}"

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, SMS_GATEWAY, email_message.encode("utf-8"))
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"SMTP send failed: {exc}") from exc


def main() -> int:
    load_dotenv()
    gmail_user = os.getenv("GMAIL_USER", "").strip()
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not gmail_user or not gmail_app_password:
        print("ERROR: Missing GMAIL_USER or GMAIL_APP_PASSWORD in environment.")
        return 1

    try:
        forecast = get_tomorrow_forecast()
        print(f"Preparing T+1 forecast for {forecast['date_iso']} ({LOCATION_NAME})")
        sms_message = format_sms_message(forecast)
        print(f"SMS length: {len(sms_message)} characters")
        send_sms_via_email(gmail_user, gmail_app_password, sms_message)
        print("Success: Forecast SMS sent.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
