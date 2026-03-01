# ai-briefing-poc

Free-first daily 08:00 KST AI briefing generator.

Output format (compact):
- 핵심 3줄
- NASDAQ 영향 1줄

## Data sources (no paid API)

- Google News RSS (broad market pulse)
- Official / media RSS·Atom feeds (configurable)
  - OpenAI News
  - Anthropic News
  - Google AI Blog
  - NVIDIA AI Blog
  - TechCrunch AI

You can replace/add feeds via `FEED_URLS`.

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

## Environment

- `NEWS_QUERY` (default: `artificial intelligence nasdaq`)
- `NEWS_COUNT` (default: `18`)
- `HTTP_TIMEOUT` (default: `15`)
- `FEED_URLS` (comma-separated RSS/Atom URLs)
- `OUTPUT_PATH` (optional output file path)

---

## 08:00 scheduling example (cron)

```bash
# KST server 기준, 매일 08:00 실행
0 8 * * * cd /path/to/ai-briefing-poc && /usr/bin/env bash -lc 'source .venv/bin/activate && python src/main.py > out/briefing-$(date +\%F).txt'
```

> Tip: If you send this output to Telegram/Discord later, keep this generator unchanged and add a separate notifier step.

---

## Heuristic notes

- Source trust score is lightweight heuristic (not absolute truth)
- NASDAQ impact line is rule-based sentiment + mega-cap mention adjustment
- For production-grade signal quality, add backtest logs and source-level weighting
