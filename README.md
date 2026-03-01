# ai-briefing-poc

POC for a daily 08:00 KST AI news briefing with:
- 3-line core summary
- 1-line NASDAQ impact (positive/neutral/negative)
- 1 action suggestion

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

## Environment

- `OPENAI_API_KEY` (optional, if using LLM summary)
- `NEWS_QUERY` (default: AI)
- `TZ` (default: Asia/Seoul)

## Next steps

1. Add reliable news sources and filters
2. Add scheduling (cron/OpenClaw heartbeat/cron job)
3. Add Telegram output formatter
4. Add backtest-like log for daily signal quality
