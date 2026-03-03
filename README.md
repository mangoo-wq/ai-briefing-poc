# ai-briefing-poc

Free-first daily 08:00 KST AI briefing generator.

## Output contract
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
  - Hacker News (hnrss)
  - GeekNews

You can replace/add feeds via `FEED_URLS`.

## Trust signals (proof-first)
### Done
- Cron-compatible daily generator is running.
- Fixed output shape is enforced (3 + 1 lines).
- Runtime logs are persisted at `out/cron.log`.

### In progress
- 7-day reliability baseline (success/failure rate).
- Repeated failure-type labeling (for weekly fixes).

### Next action
- Publish weekly reliability snapshot in the README.

### Current measured snapshot
- 2026-03-02 observed runs: **4 success / 0 failure** (source: `out/cron.log`)
- 2026-03-03 quality guardrail added: relevance filtering + source-diversity top-3 selection

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
0 8 * * * cd /path/to/ai-briefing-poc && /usr/bin/env bash -lc 'source .venv/bin/activate && python src/main.py >> out/cron.log 2>&1'
```

> Tip: Keep generation and notification decoupled. Add Telegram/Discord as a separate notifier step.

---

## Heuristic notes
- Source trust score is a lightweight heuristic (not absolute truth)
- NASDAQ impact line is rule-based sentiment + mega-cap mention adjustment
- For production-grade signal quality, add backtest logs and source-level weighting
