from __future__ import annotations

import os
import re
import textwrap
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Tuple
from urllib.parse import quote_plus, urlparse
import xml.etree.ElementTree as ET

import requests


# -----------------------------
# Config
# -----------------------------
NEWS_QUERY = os.getenv("NEWS_QUERY", "artificial intelligence nasdaq")
NEWS_COUNT = int(os.getenv("NEWS_COUNT", "18"))
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "")

# Comma-separated external RSS/Atom feeds (free)
FEED_URLS = [
    u.strip()
    for u in os.getenv(
        "FEED_URLS",
        ",".join(
            [
                "https://openai.com/news/rss.xml",
                "https://www.anthropic.com/news/rss.xml",
                "https://blog.google/technology/ai/rss/",
                "https://blogs.nvidia.com/blog/category/ai/feed/",
                "https://techcrunch.com/category/artificial-intelligence/feed/",
                "https://hnrss.org/frontpage",
                "https://feeds.feedburner.com/geeknews-feed",
            ]
        ),
    ).split(",")
    if u.strip()
]

# -----------------------------
# Heuristic trust map (0.0~1.0)
# -----------------------------
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
    "openai": 0.88,
    "anthropic": 0.88,
    "google": 0.88,
    "nvidia": 0.88,
    "sec.gov": 0.95,
    "techcrunch": 0.75,
    "the verge": 0.75,
    "forbes": 0.7,
    "yahoo finance": 0.7,
}

MEGA_CAPS = [
    "nvidia",
    "microsoft",
    "apple",
    "amazon",
    "meta",
    "google",
    "alphabet",
    "amd",
    "intel",
    "tesla",
]


def _google_news_rss_url(query: str) -> str:
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _split_title_source(raw_title: str) -> Tuple[str, str]:
    # Google News RSS titles often end with " - Source"
    parts = raw_title.rsplit(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return raw_title.strip(), "Unknown"


def _to_kst(pub_raw: str) -> str:
    if not pub_raw:
        return ""
    try:
        dt = parsedate_to_datetime(pub_raw)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return pub_raw


def fetch_google_news(query: str, limit: int = 18) -> List[Dict[str, str]]:
    url = _google_news_rss_url(query)
    r = requests.get(url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()

    root = ET.fromstring(r.text)
    items = root.findall("./channel/item")

    out: List[Dict[str, str]] = []
    for item in items[:limit]:
        raw_title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()

        title, source = _split_title_source(raw_title)
        if title:
            out.append(
                {
                    "title": title,
                    "source": source,
                    "link": link,
                    "published": _to_kst(pub_date_raw),
                }
            )
    return out


def _fetch_rss_atom(feed_url: str, limit: int = 8) -> List[Dict[str, str]]:
    r = requests.get(feed_url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    root = ET.fromstring(r.text)

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
    }

    out: List[Dict[str, str]] = []

    # RSS
    rss_items = root.findall("./channel/item")
    if rss_items:
        for item in rss_items[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_raw = (item.findtext("pubDate") or item.findtext("published") or "").strip()
            source = _domain(link) or _domain(feed_url) or "Unknown"
            if title:
                out.append(
                    {
                        "title": title,
                        "source": source,
                        "link": link,
                        "published": _to_kst(pub_raw),
                    }
                )
        return out

    # Atom
    entries = root.findall(".//atom:entry", ns)
    if entries:
        for entry in entries[:limit]:
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            link_el = entry.find("atom:link", ns)
            link = (link_el.get("href") if link_el is not None else "") or ""
            pub_raw = (
                (entry.findtext("atom:updated", default="", namespaces=ns) or "").strip()
                or (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()
            )
            source = _domain(link) or _domain(feed_url) or "Unknown"
            if title:
                out.append(
                    {
                        "title": title,
                        "source": source,
                        "link": link,
                        "published": _to_kst(pub_raw),
                    }
                )

    return out


def fetch_news(limit: int = 18) -> List[Dict[str, str]]:
    merged: List[Dict[str, str]] = []

    # 1) Google News (broad market pulse)
    try:
        merged.extend(fetch_google_news(NEWS_QUERY, limit))
    except Exception:
        pass

    # 2) Curated free feeds (official/tech media)
    for feed in FEED_URLS:
        try:
            merged.extend(_fetch_rss_atom(feed, max(3, limit // max(1, len(FEED_URLS)))))
        except Exception:
            continue

    # De-dup by normalized title
    seen = set()
    uniq: List[Dict[str, str]] = []
    for item in merged:
        key = re.sub(r"\s+", " ", item.get("title", "").strip().lower())
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(item)

    # Sort by trust desc (lightweight heuristic), then keep top N
    uniq.sort(key=lambda x: _trust_for_source(x.get("source", "Unknown")), reverse=True)
    return uniq[:limit]


def _score_sentiment(headlines: List[str]) -> int:
    positive = {
        "beat",
        "growth",
        "surge",
        "rally",
        "record",
        "profit",
        "upgrade",
        "strong",
        "expand",
        "partnership",
        "funding",
        "launch",
    }
    negative = {
        "drop",
        "fall",
        "miss",
        "lawsuit",
        "ban",
        "probe",
        "risk",
        "slowdown",
        "cut",
        "downgrade",
        "warning",
        "selloff",
        "delay",
    }

    score = 0
    for h in headlines:
        words = re.findall(r"[a-zA-Z]+", h.lower())
        score += sum(1 for w in words if w in positive)
        score -= sum(1 for w in words if w in negative)
    return score


def _trust_for_source(source: str) -> float:
    key = source.lower().strip()
    return next((v for k, v in SOURCE_TRUST.items() if k in key), 0.6)


def _source_trust_score(sources: List[str]) -> float:
    if not sources:
        return 0.5
    scores = [_trust_for_source(src) for src in sources]
    return round(sum(scores) / len(scores), 2)


def classify_nasdaq_impact(score: int, mega_cap_hits: int) -> str:
    adjusted = score + (1 if mega_cap_hits >= 2 else 0)
    if adjusted >= 3:
        return "긍정"
    if adjusted <= -3:
        return "부정"
    return "중립"


def _count_mega_cap_mentions(headlines: List[str]) -> int:
    text = " ".join(headlines).lower()
    return sum(1 for name in MEGA_CAPS if name in text)


def _format_core_3lines(news: List[Dict[str, str]]) -> List[str]:
    top = news[:3]
    lines: List[str] = []
    for i, item in enumerate(top, start=1):
        title = textwrap.shorten(item["title"], width=74, placeholder="…")
        source = item.get("source", "Unknown")
        lines.append(f"{i}) {title} ({source})")

    # pad when < 3
    while len(lines) < 3:
        lines.append(f"{len(lines)+1}) (데이터 부족)")
    return lines


def make_briefing(news: List[Dict[str, str]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not news:
        lines = [
            f"[AI Briefing] {now}",
            "핵심 3줄",
            "1) 오늘 수집된 뉴스가 없습니다.",
            "2) 무료 RSS 소스 연결 상태 점검 필요",
            "3) 임시로 전일 기준 유지",
            "NASDAQ 영향: 중립 (데이터 부족)",
        ]
        return "\n".join(lines)

    headlines = [n["title"] for n in news]
    score = _score_sentiment(headlines)
    mega_cap_hits = _count_mega_cap_mentions(headlines)
    impact = classify_nasdaq_impact(score, mega_cap_hits)

    core3 = _format_core_3lines(news)
    trust = _source_trust_score([n.get("source", "Unknown") for n in news[:3]])

    lines = [
        f"[AI Briefing] {now}",
        "핵심 3줄",
        *core3,
        f"NASDAQ 영향: {impact} (근거신뢰도 {trust})",
    ]
    return "\n".join(lines)


def main() -> None:
    news = fetch_news(NEWS_COUNT)
    result = make_briefing(news)
    print(result)

    if OUTPUT_PATH.strip():
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(result + "\n")


if __name__ == "__main__":
    main()
