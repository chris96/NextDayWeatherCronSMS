# NextDayWeatherCronSMS

Daily Python automation that sends tomorrow's weather forecast (T+1) to a phone via email-to-SMS gateway.

## Project

- Location: Statesboro, Georgia, USA
- Delivery target: `6059639101@tmomail.net` (Mint Mobile / T-Mobile network)
- Data source: Open-Meteo (no API key)
- Runtime: Python 3
- Automation: GitHub Actions scheduled workflow + manual trigger

## Repository Structure

```text
.github/
  workflows/
    weather.yml
weather-sms/
  weather_sms.py
  requirements.txt
  .env.example
  README.md
```

## Quick Start

1. Go to `weather-sms/`.
2. Create and activate a Python virtual environment.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set:
   - `GMAIL_USER`
   - `GMAIL_APP_PASSWORD`
5. Run locally:
   - `python weather_sms.py`

## Automation

The workflow file `.github/workflows/weather.yml` runs daily using UTC cron:

- `0 5 * * *` (midnight EST, 1:00 AM EDT)

It also supports manual runs with `workflow_dispatch` and a `days_ahead` input (`1` = tomorrow, `0` = today).

## Detailed Docs

See `weather-sms/README.md` for full setup and operational details.
