# Bandcamp Favorites Section Design

## Goal
Display two personal favorite Bandcamp album embeds (latest added + random) in a dedicated section below `<main>` in index.html, driven by a `data/favorites.json` list.

## Storage Format

`data/favorites.json`:
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

- User only needs to add a new `{ "url": "...", "album_id": null, "title": null }` entry
- Script resolves and caches `album_id` + `title` on first run
- Order in array = add order; last entry = latest

## Script Changes (`scripts/fetch_bandcamp_aotd.py`)

Add three new functions:
1. `resolve_favorites(path)` — reads JSON, fetches any unresolved entries, saves back
2. `pick_favorites(albums)` — returns `(latest, random_pick)` as two album dicts
3. `update_favorites_section(latest, random_pick)` — replaces placeholder in index.html

Run after existing AOTD logic in `__main__`.

## index.html Changes

Add below `</main>`:
```html
<section id="favorites">
  <div class="favorites-header">個人收藏</div>
  <div class="favorites-embeds">
    <!-- FAVORITES_EMBED_START -->
    <!-- FAVORITES_EMBED_END -->
  </div>
</section>
```

CSS: flex row, wrap on small screens, consistent with existing style.

Placeholder replaced by script with:
```html
<div class="fav-item"><div class="fav-label">最新</div><iframe ...></iframe></div>
<div class="fav-item"><div class="fav-label">隨機</div><iframe ...></iframe></div>
```

## Data Flow

```
favorites.json (URLs) → resolve_favorites() → pick latest + random
→ update_favorites_section() → index.html
```

GitHub Action already runs daily — no new workflow needed.
