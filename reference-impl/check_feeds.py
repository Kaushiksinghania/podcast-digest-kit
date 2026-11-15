#!/usr/bin/env python3
"""
check_feeds.py — return podcast episodes published inside a time window.

Reference implementation for SPEC.md §3. Only dependency: requests.

    pip install requests

Usage:
    python3 check_feeds.py --feeds feeds.json --since 76 --until 48
    python3 check_feeds.py --feeds feeds.json --since 240 --until 0      # smoke test
    python3 check_feeds.py --feeds feeds.json --since 76 --until 48 --json-out out.json

Window semantics: keep episodes published between (now - since) and (now - until) hours ago.
For a DAILY run use --since 76 --until 48. For a run every N hours use since = N+24, until = 24.

Output: JSON array on stdout, sorted oldest-first. Warnings go to stderr so the JSON stays clean.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import requests

NS = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

UA = "podcast-digest/1.0 (+https://example.com)"


def log(msg: str) -> None:
    print(f"[warn] {msg}", file=sys.stderr)


def load_feeds(path: str) -> dict:
    """Accept either {"feeds": {...}} or a flat {key: {...}} map."""
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("feeds"), dict):
        return data["feeds"]
    return {k: v for k, v in data.items() if isinstance(v, dict) and "rss" in v}


def parse_dt(raw: str | None):
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def text_of(el) -> str:
    return "".join(el.itertext()).strip() if el is not None else ""


def strip_html(s: str) -> str:
    """Many feeds ship HTML in <description>; give the agent clean prose."""
    if not s or "<" not in s:
        return s
    s = re.sub(r"(?is)<(script|style).*?</\\1>", " ", s)
    s = re.sub(r"(?i)<br\\s*/?>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = re.sub(r"[ \\t]+", " ", s)
    return s.strip()


def audio_url(item) -> str:
    for enc in item.findall("enclosure"):
        if "audio" in (enc.get("type") or ""):
            return enc.get("url") or ""
    # some feeds only carry it in itunes:duration-less form; try media:content
    for mc in item.findall("{http://search.yahoo.com/mrss/}content"):
        if "audio" in (mc.get("type") or ""):
            return mc.get("url") or ""
    return ""


def fetch(url: str, timeout: int) -> bytes:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    r.raise_for_status()
    return r.content


def main() -> int:
    ap = argparse.ArgumentParser(description="Poll podcast RSS feeds for a time window.")
    ap.add_argument("--feeds", default="feeds.json")
    ap.add_argument("--since", type=int, default=76, help="oldest edge, hours ago (default 76)")
    ap.add_argument("--until", type=int, default=48, help="newest edge, hours ago (default 48)")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--max", type=int, default=0, help="cap results (0 = no cap)")
    args = ap.parse_args()

    feeds = load_feeds(args.feeds)
    now = datetime.now(timezone.utc)
    older = now - timedelta(hours=args.since)
    newer = now - timedelta(hours=args.until)

    results, failures = [], []

    for key, meta in feeds.items():
        try:
            body = fetch(meta["rss"], args.timeout)
            root = ET.fromstring(body)
        except Exception as exc:  # a dead feed must never abort the run
            failures.append(key)
            log(f"{key}: {type(exc).__name__}: {exc}")
            continue

        channel = root.find("channel")
        if channel is None:
            log(f"{key}: no <channel>")
            continue
        fallback_podcast = text_of(channel.find("title")) or meta.get("name", key)

        for item in channel.findall("item"):
            dt = parse_dt(text_of(item.find("pubDate"))) or parse_dt(
                text_of(item.find("{%s}date" % NS["itunes"]))
            ) or parse_dt(text_of(item.find("published")))
            if dt is None or not (older <= dt <= newer):
                continue

            desc = strip_html(
                text_of(item.find("description"))
                or text_of(item.find("{%s}summary" % NS["itunes"]))
            )
            results.append(
                {
                    "feed_key": key,
                    "podcast": meta.get("name") or fallback_podcast,
                    "title": text_of(item.find("title")),
                    "published": dt.isoformat(),
                    "link": text_of(item.find("link")),
                    "guid": text_of(item.find("guid")),
                    "audio_url": audio_url(item),
                    "description": desc[:2000],
                    "website_transcripts": bool(meta.get("website_transcripts")),
                }
            )

    results.sort(key=lambda x: x["published"])
    if args.max and len(results) > args.max:
        log(f"capping {len(results)} -> {args.max} (carry the rest to the next run)")
        results = results[: args.max]

    payload = json.dumps(results, indent=2, ensure_ascii=False)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            fh.write(payload)
        log(f"wrote {len(results)} episodes -> {args.json_out}")
    else:
        print(payload)

    if failures:
        log(f"{len(failures)} feed(s) failed: {', '.join(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
