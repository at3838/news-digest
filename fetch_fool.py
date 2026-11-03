#!/usr/bin/env python3
"""Motley Fool (fool.com) direct-feed source for Andrew's news digest.

fool.com US has no public RSS feed (usual /feed/, /rss/ paths 404), but
https://www.fool.com/investing-news/ is server-rendered and reachable from
this VM (200, Mozilla UA). Each article card carries a title, a one-sentence
dek and a real article URL (fool.com truncates slugs in URLs; the hrefs on
the listing page are the canonical URLs and return 200 as-is).

Two modes:
  python3 fetch_fool.py
      Read-only: fetch, filter, dedupe against news.json, print NEW
      candidates as JSON [{title_en, dek_en, url}] (max 10). Nothing written.
  python3 fetch_fool.py --append items.json
      items.json: [{title, summary, url}] with Cantonese title/summary
      already written by the caller (translation needs language judgement, so
      it stays with the agent worker, not this script). Re-reads news.json
      fresh, appends unseen items to today's London day, runs build.py,
      commits and pushes to main (pull --rebase + one push retry; on a
      rebase conflict it aborts cleanly and exits nonzero without pushing).

Dedupe: same source + same URL anywhere in news.json (all days), so the
07:30 and 19:30 runs never re-file the same article, and this script never
touches .sync-state.json or any briefing cron's seen files.
"""
import html as htmlmod
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
LONDON = ZoneInfo("Europe/London")
SOURCE = "Motley Fool"
LIST_URL = "https://www.fool.com/investing-news/"
BASE = "https://www.fool.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
MAX_ITEMS = 10

# Clear paid-service promo markers only; ordinary "stocks to buy" analysis
# titles are the article's own content, not promos, and stay in.
PROMO_MARKERS = (
    "stock advisor",
    "moneyball",
    "superscore",
    "get access now",
    "members only",
    "join now",
    "subscribe now",
    "premium service",
)

CARD_RE = re.compile(
    r'<a[^>]*href="(/investing/20\d\d/\d\d/\d\d/[^"]*)"[^>]*>\s*'
    r"<h5[^>]*>(.*?)</h5>\s*"
    r'<div class="text-md text-gray-800">(.*?)</div>',
    re.S,
)


def fetch_page():
    req = urllib.request.Request(LIST_URL, headers={"User-Agent": UA})
    last_err = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                if "</html>" in body or "<article" in body:
                    return body
                last_err = "incomplete body"
        except Exception as e:  # noqa: BLE001 - fall through to curl fallback
            last_err = str(e)
    # curl fallback (TRMNL lesson: urllib sometimes disconnects, curl works)
    try:
        out = subprocess.run(
            ["curl", "-s", "-A", UA, "--max-time", "30", LIST_URL],
            capture_output=True, text=True, timeout=40, check=True,
        )
        if "<article" in out.stdout:
            return out.stdout
        last_err = "curl body without articles"
    except Exception as e:  # noqa: BLE001
        last_err = str(e)
    raise RuntimeError(f"failed to fetch {LIST_URL}: {last_err}")


def parse_candidates(page):
    seen_urls, cards = set(), []
    for href, title, dek in CARD_RE.findall(page):
        url = BASE + href
        if url in seen_urls:
            continue
        seen_urls.add(url)
        title = htmlmod.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        dek = htmlmod.unescape(re.sub(r"<[^>]+>", "", dek)).strip()
        if not title or not url:
            continue
        low = title.lower()
        if any(m in low for m in PROMO_MARKERS):
            continue
        cards.append({"title_en": title, "dek_en": dek, "url": url})
    return cards


def load_news():
    with open(os.path.join(HERE, "news.json"), encoding="utf-8") as f:
        return json.load(f)


def known_urls(data):
    return {
        it.get("url")
        for day in data.get("days", [])
        for it in day.get("items", [])
        if it.get("source") == SOURCE and it.get("url")
    }


def new_candidates():
    data = load_news()
    known = known_urls(data)
    return [c for c in parse_candidates(fetch_page()) if c["url"] not in known][:MAX_ITEMS]


def run(cmd, check=True):
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {r.stderr.strip()}")
    return r


def do_append(items_path):
    with open(items_path, encoding="utf-8") as f:
        items = json.load(f)
    now = datetime.now(LONDON)
    today = now.strftime("%Y-%m-%d")
    time_hhmm = now.strftime("%H:%M")

    # Sync with remote first so we never overwrite the 15-min sync's work.
    run(["git", "fetch", "origin"], check=False)
    r = run(["git", "pull", "--rebase", "origin", "main"], check=False)
    if r.returncode != 0:
        run(["git", "rebase", "--abort"], check=False)
        raise RuntimeError(f"pull --rebase failed: {r.stderr.strip()}")

    data = load_news()
    known = known_urls(data)
    fresh = []
    for it in items:
        url = it.get("url")
        if not url or url in known:
            continue
        known.add(url)
        fresh.append({
            "date": today,
            "source": SOURCE,
            "briefing": SOURCE,
            "title": it["title"],
            "summary": it["summary"],
            "url": url,
            "time": time_hhmm,
        })
    if not fresh:
        print("nothing new to append")
        return
    day = next((d for d in data["days"] if d["date"] == today), None)
    if day is None:
        day = {"date": today, "items": []}
        data["days"].append(day)
        data["days"].sort(key=lambda d: d["date"], reverse=True)
    day["items"].extend(fresh)
    with open(os.path.join(HERE, "news.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    run([sys.executable, "build.py"])
    run(["git", "add", "news.json", "index.html"])
    run(["git", "commit", "-qm", f"Motley Fool feed {today} {time_hhmm} ({len(fresh)} items)"])
    r = run(["git", "push", "origin", "main"], check=False)
    if r.returncode != 0:
        # One retry after rebase; if that still fails, leave the commit
        # local for the next run instead of forcing anything.
        rb = run(["git", "pull", "--rebase", "origin", "main"], check=False)
        if rb.returncode != 0:
            run(["git", "rebase", "--abort"], check=False)
            raise RuntimeError(f"push failed, rebase also failed: {r.stderr.strip()}")
        r = run(["git", "push", "origin", "main"], check=False)
        if r.returncode != 0:
            raise RuntimeError(f"push failed after rebase retry: {r.stderr.strip()}")
    print(f"appended {len(fresh)} Motley Fool items, pushed")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--append":
        do_append(sys.argv[2])
    else:
        try:
            cands = new_candidates()
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        print(json.dumps(cands, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
