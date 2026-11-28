#!/usr/bin/env python3
"""Print the "Podcast directory" rows that feeds.json implies, as JSON.

One row per show in feeds.json (active and parked). The run agent compares
these rows with the Notion "Podcast directory" database and adds, updates or
removes rows so the database always matches feeds.json. feeds.json is the
source of truth; never edit the directory by hand and expect it to stick.

Usage: python3 reference-impl/directory_rows.py --feeds feeds.json [--out rows.json]
"""
import argparse, json, sys


def rows(feeds_path):
    feeds = json.load(open(feeds_path, encoding="utf-8"))["feeds"]
    out = []
    for key, f in feeds.items():
        parked = bool(f.get("parked"))
        out.append({
            "Show": key,
            "Feed title": f.get("name", key),
            "Host / publisher": f.get("host", ""),
            "Status": "Parked" if parked else "Active",
            "Transcript source": f.get("transcript_source", ""),
            "Tags": f.get("categories", []),
            "RSS feed": f.get("rss", ""),
        })
    # Active first, then parked, each alphabetical.
    out.sort(key=lambda r: (r["Status"] != "Active", r["Show"].lower()))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", default="feeds.json")
    ap.add_argument("--out")
    a = ap.parse_args()
    data = json.dumps(rows(a.feeds), indent=2, ensure_ascii=False)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(data + "\n")
    else:
        sys.stdout.write(data + "\n")
