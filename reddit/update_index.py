#!/usr/bin/env python3
"""更新 Reddit 週報索引頁面"""
import os
import re

reddit_dir = "/Users/lyd/Dropbox/infoworld/reddit"
index_file = os.path.join(reddit_dir, "index.html")

# 掃描所有 HTML 檔案
tech_reports = []
music_reports = []

for f in os.listdir(reddit_dir):
    if f.startswith("reddit_tech_weekly_") and f.endswith(".html"):
        date = f.replace("reddit_tech_weekly_", "").replace(".html", "")
        tech_reports.append({"date": date, "file": f})
    elif f.startswith("reddit_music_weekly_") and f.endswith(".html"):
        date = f.replace("reddit_music_weekly_", "").replace(".html", "")
        music_reports.append({"date": date, "file": f})

# 生成 JavaScript 陣列
def to_js_array(reports):
    items = [f'{{ date: "{r["date"]}", file: "{r["file"]}" }}' for r in sorted(reports, key=lambda x: x["date"], reverse=True)]
    return "[\n                " + ",\n                ".join(items) + "\n            ]"

# 讀取並更新 index.html
with open(index_file, "r") as f:
    content = f.read()

content = re.sub(
    r'tech: \[.*?\]',
    f'tech: {to_js_array(tech_reports)}',
    content,
    flags=re.DOTALL
)
content = re.sub(
    r'music: \[.*?\]',
    f'music: {to_js_array(music_reports)}',
    content,
    flags=re.DOTALL
)

with open(index_file, "w") as f:
    f.write(content)

print(f"✅ 索引已更新：{len(tech_reports)} 篇科技、{len(music_reports)} 篇音樂")
