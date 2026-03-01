from __future__ import annotations

import os
import re
import textwrap
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Dict
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import requests


NEWS_QUERY = os.getenv("NEWS_QUERY", "artificial intelligence")
NEWS_COUNT = int(os.getenv("NEWS_COUNT", "12"))
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))


def _google_news_rss_url(query: str) -> str:
    # en-US default gives broader global market coverage
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def fetch_news(query: str, limit: int = 12) -> List[Dict[str, str]]:
    url = _google_news_rss_url(query)
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()

    root = ET.fromstring(r.text)
    items = root.findall("./channel/item")

    out: List[Dict[str, str]] = []
    for item in items[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()

        pub_date = ""
        if pub_date_raw:
            try:
                pub_date = parsedate_to_datetime(pub_date_raw).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pub_date = pub_date_raw

        if title:
            out.append({"title": title, "link": link, "published": pub_date})
    return out


def _score_sentiment(headlines: List[str]) -> int:
    positive = {
        "beat", "growth", "surge", "rally", "record", "profit", "upgrade", "strong", "expand", "partnership", "funding",
    }
    negative = {
        "drop", "fall", "miss", "lawsuit", "ban", "probe", "risk", "slowdown", "cut", "downgrade", "warning", "selloff",
    }

    score = 0
    for h in headlines:
        words = re.findall(r"[a-zA-Z]+", h.lower())
        score += sum(1 for w in words if w in positive)
        score -= sum(1 for w in words if w in negative)
    return score


def classify_nasdaq_impact(score: int) -> str:
    if score >= 3:
        return "긍정"
    if score <= -3:
        return "부정"
    return "중립"


def action_suggestion(impact: str) -> str:
    if impact == "긍정":
        return "오늘 행동: 과열 추격매수보다 분할 접근 + 핵심 대형주 중심 확인"
    if impact == "부정":
        return "오늘 행동: 신규 진입 축소, 현금 비중/손절 라인 우선 점검"
    return "오늘 행동: 방향성 확인 전까지 관망 비중 유지, 이벤트 이후 대응"


def make_briefing(news: List[Dict[str, str]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not news:
        return "\n".join(
            [
                f"[AI Briefing] {now}",
                "1) 오늘 수집된 뉴스가 없습니다.",
                "2) 네트워크/소스 상태를 점검하세요.",
                "3) 임시로 어제 브리핑 기준 유지.",
                "NASDAQ 영향: 중립",
                "오늘 행동: 관망",
            ]
        )

    top = news[:3]
    headlines = [n["title"] for n in news]
    score = _score_sentiment(headlines)
    impact = classify_nasdaq_impact(score)

    lines = [f"[AI Briefing] {now}"]
    for i, item in enumerate(top, start=1):
        title = textwrap.shorten(item["title"], width=92, placeholder="…")
        lines.append(f"{i}) {title}")

    lines.append(f"NASDAQ 영향: {impact}")
    lines.append(action_suggestion(impact))
    return "\n".join(lines)


def main() -> None:
    news = fetch_news(NEWS_QUERY, NEWS_COUNT)
    print(make_briefing(news))


if __name__ == "__main__":
    main()
