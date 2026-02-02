# RSS News Feed Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local RSS news aggregator that fetches 38 sources via GitHub Actions and displays 25 latest articles in a categorized web page.

**Architecture:** GitHub Actions runs Python script every 15 minutes to fetch RSS feeds, outputs JSON. Static HTML reads JSON and renders categorized article list with expandable summaries.

**Tech Stack:** Python 3.11, feedparser, GitHub Actions, vanilla HTML/CSS/JavaScript

---

### Task 1: Initialize Git Repository

**Files:**
- Create: `.gitignore`

**Step 1: Initialize git repo**

Run: `git init`

**Step 2: Create .gitignore**

```
__pycache__/
*.pyc
.DS_Store
.env
```

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "init: initialize repository"
```

---

### Task 2: Create Config File

**Files:**
- Create: `config.json`

**Step 1: Create config.json with all RSS sources categorized**

```json
{
  "categories": {
    "AI": [
      "https://blog.google/innovation-and-ai/models-and-research/google-deepmind/rss/",
      "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_claude.xml",
      "https://www.wired.com/feed/tag/ai/latest/rss",
      "https://plink.anyfeeder.com/mittrchina/hot"
    ],
    "科技": [
      "https://www.ithome.com.tw/rss",
      "https://techcrunch.com/feed/",
      "https://feeds.arstechnica.com/arstechnica/index",
      "https://cdn.technews.tw/feed/",
      "https://cdn.technews.tw/category/meta/feed/",
      "https://feeds.content.dowjones.io/public/rss/RSSWSJD",
      "https://www.wired.com/feed/category/business/latest/rss",
      "https://www.theguardian.com/uk/technology/rss"
    ],
    "科學": [
      "https://writings.stephenwolfram.com/feed/",
      "https://www.science.org/rss/news_current.xml",
      "https://www.science.org/action/showFeed?type=axatoc&feed=rss&jc=science",
      "https://www.nature.com/nature.rss",
      "https://journals.acoustics.jp/ast/feed/"
    ],
    "財經": [
      "https://feeds.content.dowjones.io/public/rss/socialeconomyfeed",
      "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
      "https://www.theguardian.com/uk/business/rss"
    ],
    "音樂/聲音": [
      "https://blog.freesound.org/?feed=rss2",
      "https://blog.toplap.org/feed/",
      "https://cdm.link/feed/",
      "https://www.tandfonline.com/feed/rss/tmam20",
      "https://dsp56300.wordpress.com/feed/",
      "https://www.min-on.org/zh-hant/feed/",
      "https://danielmkarlsson.com/rss.xml",
      "https://wp.nyu.edu/music_and_sound_cultures/feed/"
    ],
    "媒體/文化": [
      "https://www.twreporter.org/a/rss2.xml",
      "https://www.theguardian.com/books/booksforchildrenandteenagers/rss",
      "https://blog.archive.org/feed/",
      "https://gis.rchss.sinica.edu.tw/feed/",
      "https://www.ruanyifeng.com/blog/atom.xml",
      "https://simonwillison.net/atom/everything/",
      "https://www.wired.com/feed/category/ideas/latest/rss",
      "https://www.wired.com/feed/category/science/latest/rss"
    ]
  },
  "max_items": 25
}
```

**Step 2: Commit**

```bash
git add config.json
git commit -m "feat: add RSS source configuration"
```

---

### Task 3: Create RSS Fetch Script

**Files:**
- Create: `scripts/fetch_rss.py`

**Step 1: Create scripts directory**

Run: `mkdir -p scripts`

**Step 2: Create fetch_rss.py**

```python
#!/usr/bin/env python3
import json
import hashlib
import feedparser
from datetime import datetime, timezone
from pathlib import Path

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def parse_date(entry):
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def get_summary(entry, max_length=300):
    summary = ""
    if hasattr(entry, "summary"):
        summary = entry.summary
    elif hasattr(entry, "description"):
        summary = entry.description
    # Strip HTML tags simply
    import re
    summary = re.sub(r"<[^>]+>", "", summary)
    summary = summary.strip()
    if len(summary) > max_length:
        summary = summary[:max_length] + "..."
    return summary

def fetch_feeds(config):
    articles = []
    url_to_category = {}

    for category, urls in config["categories"].items():
        for url in urls:
            url_to_category[url] = category

    for url, category in url_to_category.items():
        try:
            print(f"Fetching: {url}")
            feed = feedparser.parse(url)
            source_name = feed.feed.get("title", url)

            for entry in feed.entries:
                link = entry.get("link", "")
                if not link:
                    continue

                article = {
                    "id": hashlib.md5(link.encode()).hexdigest()[:12],
                    "title": entry.get("title", "No title"),
                    "summary": get_summary(entry),
                    "url": link,
                    "source": source_name,
                    "category": category,
                    "published": parse_date(entry).isoformat()
                }
                articles.append(article)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

    return articles

def main():
    config = load_config()
    articles = fetch_feeds(config)

    # Sort by published date, newest first
    articles.sort(key=lambda x: x["published"], reverse=True)

    # Take top N items
    max_items = config.get("max_items", 25)
    articles = articles[:max_items]

    # Create output
    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles
    }

    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)

    with open("data/feed.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(articles)} articles to data/feed.json")

if __name__ == "__main__":
    main()
```

**Step 3: Test script locally**

Run: `pip install feedparser && python scripts/fetch_rss.py`

Expected: Script outputs "Saved 25 articles to data/feed.json"

**Step 4: Verify output**

Run: `cat data/feed.json | head -50`

Expected: JSON with `updated_at` and `articles` array

**Step 5: Commit**

```bash
git add scripts/fetch_rss.py
git commit -m "feat: add RSS fetch script"
```

---

### Task 4: Create HTML Page

**Files:**
- Create: `index.html`

**Step 1: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Infoworld</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      line-height: 1.6;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      background: #fff;
      color: #333;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid #eee;
      margin-bottom: 20px;
    }
    h1 {
      font-size: 1.5rem;
      font-weight: 600;
    }
    .updated {
      color: #888;
      font-size: 0.85rem;
    }
    .category {
      margin-bottom: 24px;
    }
    .category-header {
      font-size: 1rem;
      font-weight: 600;
      color: #555;
      margin-bottom: 8px;
      cursor: pointer;
      user-select: none;
    }
    .category-header:hover {
      color: #000;
    }
    .article-list {
      border: 1px solid #eee;
      border-radius: 4px;
    }
    .article {
      padding: 10px 14px;
      border-bottom: 1px solid #eee;
    }
    .article:last-child {
      border-bottom: none;
    }
    .article-title {
      cursor: pointer;
      color: #333;
    }
    .article-title:hover {
      color: #0066cc;
    }
    .article-title::before {
      content: "● ";
      color: #ccc;
      font-size: 0.6rem;
      vertical-align: middle;
    }
    .article-detail {
      display: none;
      margin-top: 10px;
      padding: 12px;
      background: #f9f9f9;
      border-radius: 4px;
      font-size: 0.9rem;
    }
    .article-detail.open {
      display: block;
    }
    .article-summary {
      color: #555;
      margin-bottom: 10px;
    }
    .article-meta {
      font-size: 0.8rem;
      color: #888;
    }
    .article-link {
      color: #0066cc;
      text-decoration: none;
    }
    .article-link:hover {
      text-decoration: underline;
    }
    .empty {
      color: #888;
      padding: 40px;
      text-align: center;
    }
  </style>
</head>
<body>
  <header>
    <h1>Infoworld</h1>
    <span class="updated" id="updated"></span>
  </header>
  <main id="content">
    <div class="empty">載入中...</div>
  </main>

  <script>
    const CATEGORY_ORDER = ["AI", "科技", "科學", "財經", "音樂/聲音", "媒體/文化"];
    let currentOpen = null;

    async function loadFeed() {
      try {
        const res = await fetch("data/feed.json");
        const data = await res.json();
        render(data);
      } catch (e) {
        document.getElementById("content").innerHTML =
          '<div class="empty">無法載入資料，請確認 data/feed.json 存在</div>';
      }
    }

    function render(data) {
      const updatedAt = new Date(data.updated_at);
      document.getElementById("updated").textContent =
        `最後更新：${updatedAt.toLocaleString("zh-TW")}`;

      // Group by category
      const grouped = {};
      for (const cat of CATEGORY_ORDER) {
        grouped[cat] = [];
      }
      for (const article of data.articles) {
        if (grouped[article.category]) {
          grouped[article.category].push(article);
        }
      }

      let html = "";
      for (const cat of CATEGORY_ORDER) {
        const articles = grouped[cat];
        if (articles.length === 0) continue;

        html += `<div class="category">`;
        html += `<div class="category-header">▸ ${cat} (${articles.length})</div>`;
        html += `<div class="article-list">`;

        for (const article of articles) {
          html += `
            <div class="article">
              <div class="article-title" data-id="${article.id}">${article.title}</div>
              <div class="article-detail" id="detail-${article.id}">
                <div class="article-summary">${article.summary}</div>
                <div class="article-meta">
                  來源：${article.source}<br>
                  <a href="${article.url}" target="_blank" rel="noopener" class="article-link">閱讀原文 →</a>
                </div>
              </div>
            </div>
          `;
        }

        html += `</div></div>`;
      }

      document.getElementById("content").innerHTML = html || '<div class="empty">目前沒有文章</div>';

      // Add click handlers
      document.querySelectorAll(".article-title").forEach(el => {
        el.addEventListener("click", () => {
          const id = el.dataset.id;
          const detail = document.getElementById(`detail-${id}`);

          if (currentOpen && currentOpen !== detail) {
            currentOpen.classList.remove("open");
          }

          detail.classList.toggle("open");
          currentOpen = detail.classList.contains("open") ? detail : null;
        });
      });
    }

    loadFeed();
  </script>
</body>
</html>
```

**Step 2: Test locally**

Run: `open index.html` (macOS) or open in browser

Expected: Page loads, shows categorized articles from feed.json

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add main HTML page"
```

---

### Task 5: Create GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/fetch.yml`

**Step 1: Create workflow directory**

Run: `mkdir -p .github/workflows`

**Step 2: Create fetch.yml**

```yaml
name: Fetch RSS Feeds

on:
  schedule:
    - cron: '*/15 * * * *'
  workflow_dispatch:

jobs:
  fetch:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install feedparser

      - name: Fetch RSS feeds
        run: python scripts/fetch_rss.py

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/feed.json
          git diff --staged --quiet || git commit -m "chore: update feed"
          git push
```

**Step 3: Commit**

```bash
git add .github/workflows/fetch.yml
git commit -m "feat: add GitHub Actions workflow"
```

---

### Task 6: Initial Data and Push to GitHub

**Step 1: Run fetch script to create initial data**

Run: `python scripts/fetch_rss.py`

**Step 2: Commit initial data**

```bash
git add data/feed.json
git commit -m "chore: add initial feed data"
```

**Step 3: Create GitHub repository and push**

Run:
```bash
gh repo create infoworld --private --source=. --remote=origin --push
```

Or manually:
1. Create repo on GitHub
2. `git remote add origin git@github.com:YOUR_USERNAME/infoworld.git`
3. `git push -u origin main`

**Step 4: Verify Actions workflow**

Go to GitHub repo → Actions → Run workflow manually to test

---

## Summary

After completing all tasks:
- `git pull` to get latest feed.json
- Open `index.html` in browser to view news
- GitHub Actions updates every 15 minutes
