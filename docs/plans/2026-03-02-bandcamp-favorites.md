# Bandcamp Favorites Section Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a personal favorites section to index.html showing the latest-added and a random Bandcamp album as small embeds, driven by `data/favorites.json`.

**Architecture:** Three new functions added to `scripts/fetch_bandcamp_aotd.py` resolve unresolved album URLs in `data/favorites.json` (caching IDs back to the file), pick latest + random, and write two embed iframes into a placeholder block in `index.html`. A new `<section id="favorites">` with minimal CSS is inserted after `</main>` in index.html.

**Tech Stack:** Python 3.11 stdlib (json, random, re, urllib), static HTML/CSS.

---

### Task 1: Create `data/favorites.json`

**Files:**
- Create: `data/favorites.json`

**Step 1: Create the file**

```json
{
  "albums": [
    {
      "url": "https://mathiasgrassow.bandcamp.com/album/2025-laoco-n",
      "album_id": null,
      "title": null
    }
  ]
}
```

**Step 2: Verify it parses**

```bash
python3 -c "import json; d=json.load(open('data/favorites.json')); print(len(d['albums']), 'albums')"
```
Expected: `1 albums`

**Step 3: Commit**

```bash
git add data/favorites.json
git commit -m "feat: add favorites.json with initial album"
```

---

### Task 2: Add favorites section to `index.html`

**Files:**
- Modify: `index.html:134` (inside `<style>`), `index.html:153` (after `</main>`)

**Step 1: Add CSS inside the existing `<style>` block, just before `</style>` (line 134)**

```css
    #favorites {
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid #eee;
    }
    .favorites-header {
      font-size: 0.85rem;
      font-weight: 600;
      color: #888;
      margin-bottom: 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .favorites-embeds {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .fav-item {
      flex: 1;
      min-width: 280px;
    }
    .fav-label {
      font-size: 0.75rem;
      color: #aaa;
      margin-bottom: 4px;
    }
    .fav-item iframe {
      width: 100%;
    }
```

**Step 2: Add the favorites section to `index.html` after `</main>` (line 153)**

Insert between `</main>` and the blank line before `<script>`:

```html
  <section id="favorites">
    <div class="favorites-header">個人收藏</div>
    <div class="favorites-embeds">
      <!-- FAVORITES_EMBED_START -->
      <!-- FAVORITES_EMBED_END -->
    </div>
  </section>
```

**Step 3: Verify HTML structure looks right**

```bash
grep -n "favorites\|FAVORITES" index.html
```
Expected: lines with `id="favorites"`, `FAVORITES_EMBED_START`, `FAVORITES_EMBED_END`.

**Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add favorites section placeholder to index.html"
```

---

### Task 3: Extend `scripts/fetch_bandcamp_aotd.py` with favorites logic

**Files:**
- Modify: `scripts/fetch_bandcamp_aotd.py`

**Step 1: Add `import random` at the top of the file (alongside existing imports)**

**Step 2: Add `FAVORITES` constant after `HEADERS` line**

```python
FAVORITES = ROOT / "data" / "favorites.json"
```

**Step 3: Add three new functions after `update_index()`**

```python
def resolve_favorites():
    """Fetch album_id + title for any unresolved entries and save back."""
    data = json.loads(FAVORITES.read_text(encoding="utf-8"))
    changed = False
    for album in data["albums"]:
        if album["album_id"] is None:
            print(f"Resolving: {album['url']}")
            html = fetch(album["url"])
            dt = re.search(r'data-tralbum="([^"]+)"', html)
            if not dt:
                print(f"  ⚠️  Could not resolve {album['url']}, skipping")
                continue
            tralbum = json.loads(dt.group(1).replace("&quot;", '"'))
            album["album_id"] = str(tralbum["id"])
            title_m = re.search(r"<title>([^<]+)</title>", html)
            album["title"] = title_m.group(1).strip() if title_m else album["url"]
            print(f"  ✅ {album['title']} (id={album['album_id']})")
            changed = True
    if changed:
        FAVORITES.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data["albums"]


def pick_favorites(albums):
    """Return (latest, random_pick). If only one album, both are the same."""
    resolved = [a for a in albums if a["album_id"]]
    if not resolved:
        return None, None
    latest = resolved[-1]
    random_pick = random.choice(resolved)
    return latest, random_pick


def update_favorites_section(latest, random_pick):
    """Replace FAVORITES placeholder in index.html with two embed iframes."""
    if not latest:
        print("ℹ️  No resolved favorites, skipping favorites section update")
        return
    def make_iframe(album, label):
        return (
            f'<div class="fav-item">'
            f'<div class="fav-label">{label}</div>'
            f'<iframe style="border: 0; height: 42px;" '
            f'src="https://bandcamp.com/EmbeddedPlayer/album={album["album_id"]}/size=small/bgcol=ffffff/linkcol=f171a2/transparent=true/" '
            f'seamless><a href="{album["url"]}">{album["title"]}</a></iframe>'
            f'</div>'
        )
    block = (
        "      <!-- FAVORITES_EMBED_START -->\n"
        f"      {make_iframe(latest, '最新')}\n"
        f"      {make_iframe(random_pick, '隨機')}\n"
        "      <!-- FAVORITES_EMBED_END -->"
    )
    content = INDEX.read_text(encoding="utf-8")
    updated = re.sub(
        r"      <!-- FAVORITES_EMBED_START -->.*?<!-- FAVORITES_EMBED_END -->",
        block,
        content,
        flags=re.DOTALL,
    )
    if updated == content:
        print("⚠️  FAVORITES placeholder not found in index.html")
        return
    INDEX.write_text(updated, encoding="utf-8")
    print(f"✅ Favorites updated: latest={latest['title']}, random={random_pick['title']}")
```

**Step 4: Add favorites calls to `__main__` block, after `update_index()`**

```python
    albums = resolve_favorites()
    latest, random_pick = pick_favorites(albums)
    update_favorites_section(latest, random_pick)
```

**Step 5: Run the full script locally**

```bash
cd /Users/lyd/Dropbox/infoworld
python3 scripts/fetch_bandcamp_aotd.py
```

Expected output includes:
```
Resolving: https://mathiasgrassow.bandcamp.com/album/2025-laoco-n
  ✅ <title> | Mathias Grassow (id=XXXXXXXXX)
✅ Favorites updated: latest=..., random=...
```

**Step 6: Verify `data/favorites.json` now has `album_id` filled in**

```bash
python3 -c "import json; d=json.load(open('data/favorites.json')); print(d['albums'][0])"
```
Expected: dict with non-null `album_id` and `title`.

**Step 7: Verify `index.html` placeholder was replaced**

```bash
grep -A3 "FAVORITES_EMBED_START" index.html
```
Expected: lines with `fav-item` and `EmbeddedPlayer` iframes.

**Step 8: Commit**

```bash
git add scripts/fetch_bandcamp_aotd.py data/favorites.json index.html
git commit -m "feat: add favorites resolve and embed update"
```

---

### Task 4: Push and trigger GitHub Action to verify

**Step 1: Push**

```bash
git push origin master
```

**Step 2: Trigger workflow manually**

```bash
gh workflow run bandcamp_aotd.yml --repo noworl/infoworld
```

**Step 3: Watch run**

```bash
gh run watch --repo noworl/infoworld
```

Expected: all steps green, no errors.
