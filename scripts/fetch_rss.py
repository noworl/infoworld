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

    # Group by category
    by_category = {}
    for article in articles:
        cat = article["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(article)

    # Sort each category by date and take equal amount from each
    items_per_category = config.get("items_per_category", 4)
    selected = []
    for cat, cat_articles in by_category.items():
        cat_articles.sort(key=lambda x: x["published"], reverse=True)
        selected.extend(cat_articles[:items_per_category])

    # Sort all selected by date
    selected.sort(key=lambda x: x["published"], reverse=True)
    articles = selected

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
