# RSS News Feed 設計文件

## 概述

建立一個本地可瀏覽的 RSS 新聞聚合頁面，透過 GitHub Actions 每 15 分鐘自動抓取更新。

## 需求

- 顯示 25 則最新文章標題
- 依主題分類顯示（AI、科技、科學、財經、音樂/聲音、媒體/文化）
- 點擊標題展開摘要，可連結至原文
- 極簡淺色風格
- 新文章進來時，移除最舊的一則

## 架構

```
GitHub Actions (每 15 分鐘)
    │
    ▼
fetch_rss.py 抓取 38 個 RSS 來源
    │
    ▼
產出 data/feed.json + commit push
    │
    ▼
本地 git pull → 開啟 index.html
```

## 檔案結構

```
infoworld/
├── .github/workflows/fetch.yml   # GitHub Actions 設定
├── scripts/fetch_rss.py          # RSS 抓取腳本
├── data/feed.json                # 產出的文章資料
├── index.html                    # 主頁面
└── config.json                   # RSS 來源與分類設定
```

## 資料格式

### config.json

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

### feed.json

```json
{
  "updated_at": "2026-02-02T10:30:00Z",
  "articles": [
    {
      "id": "hash-of-url",
      "title": "文章標題",
      "summary": "文章摘要（截斷至 300 字）",
      "url": "https://example.com/article",
      "source": "Google DeepMind",
      "category": "AI",
      "published": "2026-02-02T09:00:00Z"
    }
  ]
}
```

## 頁面介面

- 頂部顯示標題與最後更新時間
- 依分類分組顯示，每個分類可收合
- 點擊標題展開摘要，同時只展開一則
- 摘要區塊內顯示來源與「閱讀原文」連結
- 極簡淺色風格（白底黑字）

## GitHub Actions

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
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install feedparser requests
      - run: python scripts/fetch_rss.py
      - name: Commit changes
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add data/feed.json
          git diff --staged --quiet || git commit -m "Update feed"
          git push
```

## 錯誤處理

- 單一 RSS 來源抓取失敗不影響其他來源
- 無法解析的來源跳過並記錄到 Actions log
