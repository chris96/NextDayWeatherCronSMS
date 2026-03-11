# NextDayWeatherCronSMS

Daily Python automation that sends tomorrow's weather forecast (T+1) to a phone via email-to-SMS gateway.

## Branch Goal (`codex/formatting-text`)

This branch focuses on improving SMS text formatting so messages are more visually pleasing while staying concise and reliable for carrier delivery.

## Text Formatting Options

1. Compact multiline (implemented)
   - Keep 4-5 short lines with clear labels, e.g. `High 71F Low 52F`, `Rain 30%`.
   - Best balance of readability and low character count.
2. Emoji-lite style
   - Use 1-2 symbols, e.g. `H:71F L:52F`, `Rain:30%`, `Summary`.
   - More personality, but some carriers/devices may render inconsistently.
3. Single-line summary fallback (implemented)
   - One line under 160 chars for strict delivery safety.
   - Most robust, but least readable.

## Overview

- Location: Statesboro, Georgia, USA
- Delivery target: `6059639101@tmomail.net` (Mint Mobile / T-Mobile network)
- Data source: Open-Meteo (no API key)
- Runtime: Python 3
- Automation: GitHub Actions scheduled workflow + manual trigger
- Includes:
  - Forecast date
  - High temperature
  - Low temperature
  - Chance of precipitation
  - Short weather summary

## Repository Structure

```text
.github/
  workflows/
    weather.yml
weather-sms/
  weather_sms.py
  requirements.txt
  .env.example
```

## Install Dependencies

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r weather-sms/requirements.txt
```

## Create `.env`

1. Copy `weather-sms/.env.example` to `weather-sms/.env`.
2. Fill in your Gmail credentials:

```env
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

Notes:
- Use a Gmail App Password (not your normal account password).
- Keep `.env` local and private.

## Test Locally

From the `weather-sms/` directory:

```bash
python weather_sms.py
```

Optional manual offset:

```bash
# 1 = tomorrow (default), 0 = today, 2 = day after tomorrow
python weather_sms.py 1
```

## Automation

Workflow file: `.github/workflows/weather.yml`

- Runs on schedule with:
  - `cron: "57 2 * * *"`
- Also supports manual run via `workflow_dispatch`.
- Manual run supports an input:
  - `days_ahead` (`1` = tomorrow, `0` = today)
  - `force_single_line` (`true`/`false`) to test single-line fallback format
- Installs dependencies and executes `python weather_sms.py`.

Important timezone note:
- GitHub cron is UTC.
- `57 2 * * *` is 10:57 PM Eastern Daylight Time (EDT, UTC-4).
- During Standard Time (EST, UTC-5), this runs at 9:57 PM Eastern.

## Required GitHub Secrets

Set these repository secrets:

- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`

If you see `Application-specific password required`:
- Enable Google 2-Step Verification on the Gmail account.
- Create a Gmail App Password.
- Store that 16-character app password in `GMAIL_APP_PASSWORD` (no spaces).
