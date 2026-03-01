from __future__ import annotations

import os
import re
import textwrap
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Tuple
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import requests


NEWS_QUERY = os.getenv("NEWS_QUERY", "artificial intelligence nasdaq")
NEWS_COUNT = int(os.getenv("NEWS_COUNT", "15"))
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))

# Lightweight source quality map (0.0 ~ 1.0)
SOURCE_TRUST = {
    "reuters": 0.95,
    "bloomberg": 0.95,
    "the wall street journal": 0.9,
    "wsj": 0.9,
    "financial times": 0.9,
    "cnbc": 0.85,
    "the new york times": 0.85,
    "nytimes": 0.85,
    "bbc": 0.85,
    "associated press": 0.85,
    "ap": 0.85,
    "techcrunch": 0.75,
    "the verge": 0.75,
    "forbes": 0.7,
    "yahoo finance": 0.7,
}

MEGA_CAPS = ["nvidia", "microsoft", "apple", "amazon", "meta", "google", "alphabet", "amd", "intel", "tesla"]


def _google_news_rss_url(query: str) -> str:
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def _split_title_source(raw_title: str) -> Tuple[str, str]:
    # Google News RSS titles often end with " - Source"
    parts = raw_title.rsplit(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return raw_title.strip(), "Unknown"


def fetch_news(query: str, limit: int = 15) -> List[Dict[str, str]]:
    url = _google_news_rss_url(query)
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()

    root = ET.fromstring(r.text)
    items = root.findall("./channel/item")

    out: List[Dict[str, str]] = []
    for item in items[:limit]:
        raw_title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()

        title, source = _split_title_source(raw_title)

        pub_date = ""
        if pub_date_raw:
            try:
                pub_date = parsedate_to_datetime(pub_date_raw).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pub_date = pub_date_raw

        if title:
            out.append(
                {
                    "title": title,
                    "source": source,
                    "link": link,
                    "published": pub_date,
                }
            )
    return out


def _score_sentiment(headlines: List[str]) -> int:
    positive = {
        "beat", "growth", "surge", "rally", "record", "profit", "upgrade", "strong", "expand", "partnership", "funding", "launch",
    }
    negative = {
        "drop", "fall", "miss", "lawsuit", "ban", "probe", "risk", "slowdown", "cut", "downgrade", "warning", "selloff", "delay",
    }

    score = 0
    for h in headlines:
        words = re.findall(r"[a-zA-Z]+", h.lower())
        score += sum(1 for w in words if w in positive)
        score -= sum(1 for w in words if w in negative)
    return score


def _source_trust_score(sources: List[str]) -> float:
    if not sources:
        return 0.5

    scores = []
    for src in sources:
        key = src.lower().strip()
        matched = next((v for k, v in SOURCE_TRUST.items() if k in key), 0.6)
        scores.append(matched)
    return round(sum(scores) / len(scores), 2)


def _confidence_label(score: float) -> str:
    if score >= 0.85:
        return "상"
    if score >= 0.72:
        return "중"
    return "하"


def classify_nasdaq_impact(score: int, mega_cap_hits: int) -> str:
    # Penalize / reward impact when mega-cap names appear in headlines.
    adjusted = score + (1 if mega_cap_hits >= 2 else 0)
    if adjusted >= 3:
        return "긍정"
    if adjusted <= -3:
        return "부정"
    return "중립"


def action_suggestion(impact: str) -> str:
    if impact == "긍정":
        return "오늘 행동: 추격매수 금지, 분할 접근 + 핵심주 중심"
    if impact == "부정":
        return "오늘 행동: 신규진입 축소, 현금/손절 라인 우선"
    return "오늘 행동: 관망 비중 유지, 이벤트 확인 후 대응"


def _count_mega_cap_mentions(headlines: List[str]) -> int:
    text = " ".join(headlines).lower()
    return sum(1 for name in MEGA_CAPS if name in text)


def make_briefing(news: List[Dict[str, str]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not news:
        return "\n".join(
            [
                f"[AI Briefing] {now}",
                "1) 오늘 수집된 뉴스가 없습니다.",
                "2) 네트워크/소스 상태 점검 필요",
                "3) 임시로 전일 기준 유지",
                "근거 신뢰도: 하 (소스 부족)",
                "NASDAQ 영향: 중립",
                "리스크 체크: [ ] 손절라인 [ ] 분할원칙 [ ] 포지션 과다 여부",
            ]
        )

    top = news[:3]
    headlines = [n["title"] for n in news]
    score = _score_sentiment(headlines)
    mega_cap_hits = _count_mega_cap_mentions(headlines)
    impact = classify_nasdaq_impact(score, mega_cap_hits)

    top_sources = [n.get("source", "Unknown") for n in top]
    trust = _source_trust_score(top_sources)
    confidence = _confidence_label(trust)

    lines = [f"[AI Briefing] {now}"]
    for i, item in enumerate(top, start=1):
        title = textwrap.shorten(item["title"], width=70, placeholder="…")
        source = item.get("source", "Unknown")
        lines.append(f"{i}) {title} ({source})")

    lines.append(f"근거 신뢰도: {confidence} (소스평균 {trust})")
    lines.append(f"NASDAQ 영향: {impact}")
    lines.append(action_suggestion(impact))
    lines.append("리스크 체크: [ ] 손절라인 [ ] 분할원칙 [ ] 포지션 과다 여부")
    return "\n".join(lines)


def main() -> None:
    news = fetch_news(NEWS_QUERY, NEWS_COUNT)
    print(make_briefing(news))


if __name__ == "__main__":
    main()
