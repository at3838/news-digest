#!/usr/bin/env python3
"""Build index.html for Andrew's news digest page from news.json.

Jocelin-style layout: newest day first, items grouped by source within the
day. Each item: title (linked when an original URL exists), 1-2 sentence
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
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang HK","Microsoft JhengHei",sans-serif;max-width:760px;margin:0 auto;padding:24px 16px 64px;color:#222;background:#fff;line-height:1.75;font-size:18px}
h1{font-size:30px;margin-bottom:4px}
.sub{color:#666;font-size:16px;margin-bottom:32px}
h2{font-size:24px;border-top:2px solid #222;padding-top:16px;margin-top:40px}
h3{font-size:19px;color:#444;margin:24px 0 8px}
article{margin:0 0 16px}
article .t{font-size:19px;font-weight:600}
article .t a{color:#1a56db;text-decoration:none}
article .t a:hover{text-decoration:underline}
article p{margin:4px 0;color:#333}
.meta{font-size:15px;color:#888}
.note{color:#666;background:#f6f6f6;padding:16px;border-radius:8px}
.toc{background:#f6f6f6;padding:16px;border-radius:8px;margin-bottom:8px}
.toc .day{margin-bottom:8px}
.toc .day:last-child{margin-bottom:0}
.toc a{color:#1a56db;text-decoration:none}
.toc a:hover{text-decoration:underline}
footer{margin-top:48px;font-size:15px;color:#999;border-top:1px solid #ddd;padding-top:12px}
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
            groups.setdefault(it.get("source", "其他"), []).append(it)
        day_groups.append((day, groups))
    if day_groups:
        parts.append('<div class="toc"><strong>目錄</strong>')
        for day, groups in day_groups:
            day_id = f"day-{day['date']}"
            links = " · ".join(
                f'<a href="#{day_id}-s{i}">{html.escape(src)}</a>'
                for i, src in enumerate(groups)
            )
            parts.append(
                f'<div class="day"><a href="#{day_id}">{html.escape(fmt_date(day["date"]))}</a>：{links}</div>'
            )
        parts.append("</div>")
    for day, groups in day_groups:
        day_id = f"day-{day['date']}"
        parts.append(f'<h2 id="{day_id}">{html.escape(fmt_date(day["date"]))}</h2>')
        for i, (source, items) in enumerate(groups.items()):
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
                if briefing:
                    meta_bits.append(briefing)
                parts.append(
                    f"<article><div class=\"t\">{t}</div>"
                    f"<p>{summary}</p>"
                    f"<div class=\"meta\">{' · '.join(meta_bits)}</div></article>"
                )

    parts.append(
        f"<footer>最後更新：{updated}。股價表、板塊資金流、財報數字表等數據類 briefing 唔入呢頁，"
        "淨係收新聞內容類摘要。</footer></body></html>"
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
