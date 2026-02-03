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
    max_items = config.get("max_items_per_category", 25)

    # Group by category
    by_category = {}
    for article in articles:
        cat = article["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(article)

    # Sort each category by date and take top N
    categories_output = {}
    for cat, cat_articles in by_category.items():
        cat_articles.sort(key=lambda x: x["published"], reverse=True)
        # Remove category field from each article (no longer needed)
        for a in cat_articles:
            del a["category"]
        categories_output[cat] = cat_articles[:max_items]

    # Create output
    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "categories": categories_output
    }

    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)

    with open("data/feed.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in categories_output.values())
    print(f"Saved {total} articles to data/feed.json")

if __name__ == "__main__":
    main()
