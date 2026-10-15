# Weekly OTT Telegram Digest

A GitHub Actions project that sends a weekly OTT release digest to Telegram.

It gathers Google News coverage for Telugu, Tamil, Hindi, Malayalam and English releases, asks
Gemini to verify and format the shortlist, then sends the result to Telegram every Friday at 5 PM
Berlin time.

## Setup

Create a Telegram bot with [BotFather](https://t.me/BotFather), send it a message, then obtain
your chat ID with `getUpdates`. In the repository, add these Actions secrets:

- `GEMINI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Run **Weekly OTT digest** from the Actions tab once to test the setup. Scheduled runs do not depend
on a personal computer being on.

## Run locally

Python's standard library is enough:

```bash
export GEMINI_API_KEY="..."
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python3 main.py --send
```

Use `--raw` to inspect the Google News leads without calling Gemini, or `--end-date YYYY-MM-DD` to
generate a digest for a previous Friday.
