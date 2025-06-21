from __future__ import annotations
"""Utility helpers for scraper v2 (dedup + HTTP cache)."""
import json, pathlib, hashlib, logging, time
from typing import Dict, Tuple, Optional

ROOT = pathlib.Path(__file__).resolve().parent
CACHE_DIR = ROOT / "_cache"
CACHE_DIR.mkdir(exist_ok=True)

VISITED_PATH = CACHE_DIR / "visited_hashes.json"
ETAG_PATH = CACHE_DIR / "feed_etags.json"

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Visited hash helpers
# ---------------------------------------------------------------------------

def _load_json(path: pathlib.Path) -> Dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}

def _save_json(path: pathlib.Path, data: Dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


class DedupStore:
    def __init__(self, max_size: int = 5000):
        self.max_size = max_size
        self.store = _load_json(VISITED_PATH)

    def _trim(self):
        if len(self.store) > self.max_size:
            # keep most recent N
            items = sorted(self.store.items(), key=lambda kv: kv[1], reverse=True)
            self.store = dict(items[: self.max_size])

    def seen(self, title: str) -> bool:
        h = hashlib.sha1(title.lower().encode("utf-8")).hexdigest()
        if h in self.store:
            return True
        # mark
        self.store[h] = int(time.time())
        self._trim()
        _save_json(VISITED_PATH, self.store)
        return False


# ---------------------------------------------------------------------------
# Feed ETag cache
# ---------------------------------------------------------------------------

class FeedCache:
    def __init__(self):
        self.data = _load_json(ETAG_PATH)

    def get_headers(self, url: str) -> Dict[str, str]:
        meta = self.data.get(url, {})
        headers = {}
        if "etag" in meta:
            headers["If-None-Match"] = meta["etag"]
        if "modified" in meta:
            headers["If-Modified-Since"] = meta["modified"]
        return headers

    def update(self, url: str, response):
        meta = {}
        if "ETag" in response.headers:
            meta["etag"] = response.headers["ETag"]
        if "Last-Modified" in response.headers:
            meta["modified"] = response.headers["Last-Modified"]
        if meta:
            self.data[url] = meta
            _save_json(ETAG_PATH, self.data) 