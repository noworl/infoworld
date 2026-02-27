# Bandcamp Album of the Day Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fetch today's Album of the Day from daily.bandcamp.com and auto-update the Bandcamp embed iframe in index.html daily via GitHub Action.

**Architecture:** A Python script (`scripts/fetch_bandcamp_aotd.py`) scrapes three pages in sequence: the listing page → review page → album page, extracting the numeric album ID, then patches `index.html` with regex. A GitHub Action runs it daily at midnight UTC and commits the result.

**Tech Stack:** Python 3.11, `urllib` + `re` (stdlib only, no extra deps), GitHub Actions cron schedule.

---

### Task 1: Write the scraper script

**Files:**
- Create: `scripts/fetch_bandcamp_aotd.py`

**Step 1: Create the script**

```python
#!/usr/bin/env python3
"""Fetch Bandcamp Album of the Day and update the embed iframe in index.html."""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
INDEX = ROOT / "index.html"
BASE = "https://daily.bandcamp.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req).read().decode("utf-8")


def get_review_url():
    html = fetch(f"{BASE}/album-of-the-day")
    m = re.search(r'href="(/album-of-the-day/[^"]+review[^"]*?)"', html)
    if not m:
        raise RuntimeError("Could not find review link on album-of-the-day page")
    return BASE + m.group(1)


def get_album_url(review_url):
    html = fetch(review_url)
    m = re.search(r'href="(https://[^"]+\.bandcamp\.com/album/[^"]+)"', html)
    if not m:
        raise RuntimeError(f"Could not find album URL on review page: {review_url}")
    return m.group(1)


def get_album_id_and_title(album_url):
    html = fetch(album_url)
    id_m = re.search(r"EmbeddedPlayer/album=(\d+)", html)
    if not id_m:
        raise RuntimeError(f"Could not find album ID on album page: {album_url}")
    title_m = re.search(r"<title>([^<]+)</title>", html)
    title = title_m.group(1).strip() if title_m else "Album of the Day"
    return id_m.group(1), title, album_url


def update_index(album_id, title, album_url):
    content = INDEX.read_text(encoding="utf-8")
    new_iframe = (
        f'<iframe style="border: 0; width: 100%; height: 42px;" '
        f'src="https://bandcamp.com/EmbeddedPlayer/album={album_id}/size=small/bgcol=ffffff/linkcol=f171a2/transparent=true/" '
        f'seamless><a href="{album_url}">{title}</a></iframe>'
    )
    updated = re.sub(
        r'<iframe[^>]+bandcamp\.com/EmbeddedPlayer[^>]+>.*?</iframe>',
        new_iframe,
        content,
        flags=re.DOTALL,
    )
    if updated == content:
        print("⚠️  No iframe found to replace in index.html")
        return
    INDEX.write_text(updated, encoding="utf-8")
    print(f"✅ Updated embed: {title} (album={album_id})")


if __name__ == "__main__":
    review_url = get_review_url()
    print(f"Review: {review_url}")
    album_url = get_album_url(review_url)
    print(f"Album: {album_url}")
    album_id, title, album_url = get_album_id_and_title(album_url)
    print(f"ID: {album_id}, Title: {title}")
    update_index(album_id, title, album_url)
```

**Step 2: Run locally to verify**

```bash
cd /Users/lyd/Dropbox/infoworld
python3 scripts/fetch_bandcamp_aotd.py
```

Expected output:
```
Review: https://daily.bandcamp.com/album-of-the-day/...
Album: https://....bandcamp.com/album/...
ID: XXXXXXXXX, Title: Album Name | Artist
✅ Updated embed: ...
```

**Step 3: Verify index.html changed**

```bash
grep "EmbeddedPlayer" index.html
```

Expected: new album ID in the src attribute.

**Step 4: Commit**

```bash
git add scripts/fetch_bandcamp_aotd.py index.html
git commit -m "feat: add Bandcamp Album of the Day scraper"
```

---

### Task 2: Add GitHub Action workflow

**Files:**
- Create: `.github/workflows/bandcamp_aotd.yml`

**Step 1: Create the workflow**

```yaml
name: Bandcamp Album of the Day

on:
  schedule:
    - cron: '0 0 * * *'   # daily at midnight UTC
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Fetch Album of the Day
        run: python scripts/fetch_bandcamp_aotd.py

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add index.html
          git diff --staged --quiet || git commit -m "chore: update bandcamp album of the day"
          git push
```

**Step 2: Commit**

```bash
git add .github/workflows/bandcamp_aotd.yml
git commit -m "feat: add Bandcamp AOTD GitHub Action"
```

**Step 3: Push and verify**

```bash
git push origin master
```

Then go to GitHub → Actions → "Bandcamp Album of the Day" → Run workflow (workflow_dispatch) to test manually.
