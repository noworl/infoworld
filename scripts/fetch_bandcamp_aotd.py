#!/usr/bin/env python3
"""Fetch Bandcamp Album of the Day and update the embed iframe in index.html."""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
INDEX = ROOT / "index.html"
BASE = "https://daily.bandcamp.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8")


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
    # Album ID is in data-tralbum JSON attribute (most reliable source)
    dt = re.search(r'data-tralbum="([^"]+)"', html)
    if not dt:
        raise RuntimeError(f"Could not find data-tralbum on album page: {album_url}")
    tralbum = json.loads(dt.group(1).replace("&quot;", '"'))
    album_id = str(tralbum["id"])
    title_m = re.search(r"<title>([^<]+)</title>", html)
    title = title_m.group(1).strip() if title_m else "Album of the Day"
    return album_id, title


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
        print("ℹ️  index.html already up to date, no changes needed")
        return
    INDEX.write_text(updated, encoding="utf-8")
    print(f"✅ Updated embed: {title} (album={album_id})")


if __name__ == "__main__":
    review_url = get_review_url()
    print(f"Review: {review_url}")
    album_url = get_album_url(review_url)
    print(f"Album: {album_url}")
    album_id, title = get_album_id_and_title(album_url)
    print(f"ID: {album_id}, Title: {title}")
    update_index(album_id, title, album_url)
