#!/usr/bin/env python3
"""Build index.html for Andrew's news digest page from news.json.

Jocelin-style layout: newest day first, items grouped by source within the
day. Within a day, source groups are ordered by their latest item time,
newest first (so the day's latest briefing leads the page); items inside a
group keep briefing order for equal times, newest briefing first otherwise.
Each item: title (linked when an original URL exists), 1-2 sentence
Cantonese summary, source meta line. Light mode only, Traditional Chinese.
"""
import html
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
LONDON = ZoneInfo("Europe/London")

WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

# 來源名歸一：同步嗰陣來源名偶爾差一個空格，頁面分組係按字串精確分，
# 唔歸一就會同一個來源出兩個掣。key 係舊寫法，value 係正名（跟 SYNC.md 入選表）。
SOURCE_ALIASES = {
    "Gmail股市信件": "Gmail 股市信件",
}


def fmt_date(date_str):
    y, m, d = (int(p) for p in date_str.split("-"))
    wd = WEEKDAY[datetime(y, m, d).weekday()]
    return f"{y}年{m}月{d}日（{wd}）"


def render(data):
    days = data.get("days", [])
    days = sorted(days, key=lambda d: d["date"], reverse=True)
    updated = datetime.now(LONDON).strftime("%Y年%m月%d日 %H:%M（倫敦時間）")

    parts = []
    parts.append("""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Andrew 的每日新聞摘要</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang HK","Microsoft JhengHei",sans-serif;max-width:760px;margin:0 auto;padding:24px 16px 64px;color:#222;background:#f3ead8;line-height:1.75;font-size:20px}
h1{font-size:26px;margin-bottom:4px}
.sub{color:#666;font-size:18px;margin-bottom:32px}
h2{font-size:28px;border-top:2px solid #222;padding-top:16px;margin-top:40px}
h3{font-size:22px;color:#444;margin:24px 0 8px}
article{margin:0 0 16px}
article .t{font-size:22px;font-weight:600}
article .t a{color:#1a56db;text-decoration:none}
article .t a:hover{text-decoration:underline}
article p{margin:4px 0;color:#333}
.meta{font-size:17px;color:#888}
.note{color:#666;background:#e9dcbe;padding:16px;border-radius:8px}
.filters{margin-bottom:16px}
.filter-btn{font-size:16px;padding:6px 12px;margin:0 8px 8px 0;border:1px solid #999;border-radius:20px;background:#fff;cursor:pointer}
.filter-btn.active{background:#222;color:#fff;border-color:#222}
footer{margin-top:48px;font-size:17px;color:#999;border-top:1px solid #ddd;padding-top:12px}
</style>
</head>
<body>
<h1>Andrew 的每日新聞摘要</h1>
<div class="sub">財經＋科技新聞摘要總匯。來源係每日經 WhatsApp 收到嘅新聞 briefing，自動歸檔，最新一日行先。</div>
""")

    if not days:
        parts.append(
            '<div class="note">由 2026 年 11 月 2 號起，WhatsApp 收到嘅新聞摘要會自動歸檔落呢度。'
            "朝早 briefing 送出之後，呢頁就會出現今日第一批內容。</div>"
        )
    # group items by source per day first, so the directory and the body share it
    day_groups = []
    for day in days:
        groups = {}
        for it in day.get("items", []):
            src = SOURCE_ALIASES.get(it.get("source", "其他"), it.get("source", "其他"))
            groups.setdefault(src, []).append(it)
        # within a group: newest briefing first (stable, so equal times keep
        # briefing order); groups: newest latest-item time first.
        # Missing time sorts last ("00:00").
        ordered = {}
        for source, items in groups.items():
            items.sort(key=lambda it: it.get("time") or "00:00", reverse=True)
            ordered[source] = items
        groups = dict(sorted(
            ordered.items(),
            key=lambda kv: max(it.get("time") or "00:00" for it in kv[1]),
            reverse=True,
        ))
        day_groups.append((day, groups))
    if day_groups:
        seen = []
        for _, groups in day_groups:
            for src in groups:
                if src not in seen:
                    seen.append(src)
        btns = ['<button class="filter-btn active" data-filter="全部">全部</button>']
        for src in seen:
            btns.append(
                f'<button class="filter-btn" data-filter="{html.escape(src, quote=True)}">{html.escape(src)}</button>'
            )
        parts.append('<div class="filters"><strong>來源：</strong>' + " ".join(btns) + "</div>")
    for day, groups in day_groups:
        day_id = f"day-{day['date']}"
        parts.append(f'<h2 id="{day_id}">{html.escape(fmt_date(day["date"]))}</h2>')
        for i, (source, items) in enumerate(groups.items()):
            parts.append(f'<section data-source="{html.escape(source, quote=True)}">')
            parts.append(f'<h3 id="{day_id}-s{i}">{html.escape(source)}</h3>')
            for it in items:
                title = html.escape(it.get("title", ""))
                summary = html.escape(it.get("summary", ""))
                url = it.get("url")
                briefing = html.escape(it.get("briefing", ""))
                if url:
                    t = f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{title}</a>'
                else:
                    t = title
                meta_bits = [f"來源：{html.escape(source)}"]
                if it.get("date"):
                    y, m, d = (int(p) for p in it["date"].split("-"))
                    dt = f"{y}年{m}月{d}日"
                    if it.get("time"):
                        dt += f" {it['time']}"
                    meta_bits.append(f"{html.escape(dt)}")
                elif it.get("time"):
                    meta_bits.append(f"{html.escape(it['time'])}")
                parts.append(
                    f"<article><div class=\"t\">{t}</div>"
                    f"<p>{summary}</p>"
                    f"<div class=\"meta\">{' · '.join(meta_bits)}</div></article>"
                )
            parts.append("</section>")

    parts.append(
        f"<footer>最後更新：{updated}。股價表、板塊資金流、財報數字表等數據類 briefing 唔入呢頁，"
        "淨係收新聞內容類摘要。</footer>"
        "<script>"
        "function setFilter(src){"
        "document.querySelectorAll('.filter-btn').forEach(function(b){b.classList.toggle('active',b.dataset.filter===src);});"
        "document.querySelectorAll('section[data-source]').forEach(function(sec){sec.style.display=(src==='\u5168\u90e8'||sec.dataset.source===src)?'':'none';});"
        "document.querySelectorAll('h2[id^=\"day-\"]').forEach(function(h){var el=h.nextElementSibling,vis=false;"
        "while(el&&el.tagName!=='H2'){if(el.tagName==='SECTION'&&el.style.display!=='none'){vis=true;break;}el=el.nextElementSibling;}"
        "h.style.display=vis?'':'none';});"
        "}"
        "document.querySelectorAll('.filter-btn').forEach(function(b){b.addEventListener('click',function(){setFilter(b.dataset.filter);});});"
        "</script></body></html>"
    )
    return "\n".join(parts) + "\n"


def main():
    with open(os.path.join(HERE, "news.json"), encoding="utf-8") as f:
        data = json.load(f)
    out = render(data)
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print(f"built index.html: {len(data.get('days', []))} days, "
          f"{sum(len(d.get('items', [])) for d in data.get('days', []))} items")


if __name__ == "__main__":
    main()
