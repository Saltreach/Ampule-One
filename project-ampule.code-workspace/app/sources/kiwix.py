"""
Kiwix ZIM knowledge base downloader and article extractor.

Downloads offline ZIM archives from the Kiwix library and extracts
article text for ingestion into the Project Ampule RAG pipeline.

Requires:  libzim       (pip install libzim)
Already needed: beautifulsoup4, requests
"""

import re
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

try:
    from libzim.reader import Archive
    HAS_LIBZIM = True
except ImportError:
    Archive = None
    HAS_LIBZIM = False

# ── Paths ─────────────────────────────────────────────────────────────────────
# Resolved from this file's location: app/sources/kiwix.py → 3 levels up = project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
KIWIX_DIR = _PROJECT_ROOT / "data" / "kiwix"

# ── Kiwix OPDS catalog ────────────────────────────────────────────────────────
CATALOG_URL = "https://library.kiwix.org/catalog/v2/entries"
_ATOM = "http://www.w3.org/2005/Atom"
_DC   = "http://purl.org/dc/terms/"

# ── Curated packs ─────────────────────────────────────────────────────────────
# Book names are the stable base names used in Kiwix filenames
# (date suffixes like _2024-07 are stripped automatically).
PACKS = {
    "essential": {
        "label":       "Essential  (~2–5 GB)",
        "description": "Wikipedia Medicine + all English Wikibooks "
                       "(first aid manuals, survival guides, field references).",
        "books": [
            "wikipedia_en_medicine",
            "wikibooks_en_all",
        ],
    },
    "comprehensive": {
        "label":       "Comprehensive  (~12–20 GB)",
        "description": "Adds full English Wikipedia (no images) and Wikivoyage "
                       "for regional travel and geography.",
        "books": [
            "wikipedia_en_medicine",
            "wikibooks_en_all",
            "wikipedia_en_all_nopic",
            "wikivoyage_en_all",
        ],
    },
    "full": {
        "label":       "Full  (32 GB+)",
        "description": "Full English Wikipedia with images plus everything above. "
                       "Maximum offline knowledge.",
        "books": [
            "wikipedia_en_medicine",
            "wikibooks_en_all",
            "wikipedia_en_all_maxi",
            "wikivoyage_en_all",
        ],
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _human_size(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _base_name(url):
    """
    Derive the stable book name from a Kiwix download URL.
    e.g. '.../wikipedia_en_medicine_2024-07.zim' → 'wikipedia_en_medicine'
    """
    stem = Path(url).stem                          # wikipedia_en_medicine_2024-07
    return re.sub(r"_\d{4}-\d{2}$", "", stem)      # wikipedia_en_medicine


# ── Catalog ───────────────────────────────────────────────────────────────────

def fetch_catalog(lang="eng", page_size=500):
    """
    Query the Kiwix OPDS catalog and return a dict of
    { base_name: book_info } for all available books.
    """
    params = {"lang": lang, "count": page_size}
    r = requests.get(CATALOG_URL, params=params, timeout=30)
    r.raise_for_status()

    root = ET.fromstring(r.content)
    books = {}

    for entry in root.findall(f"{{{_ATOM}}}entry"):
        title = entry.findtext(f"{{{_ATOM}}}title", "").strip()

        # Find the ZIM download link
        download_url = None
        size_bytes = 0
        for link in entry.findall(f"{{{_ATOM}}}link"):
            href = link.get("href", "")
            ltype = link.get("type", "")
            if href.endswith(".zim") or "zim" in ltype:
                download_url = href
                size_bytes = int(link.get("length") or 0)
                break

        if not download_url:
            continue

        name = _base_name(download_url)
        filename = Path(download_url).name

        # When the same base name appears multiple times (different snapshots),
        # keep the entry with the largest file (most recent/complete).
        if name not in books or size_bytes > books[name]["size_bytes"]:
            books[name] = {
                "name":       name,
                "title":      title,
                "url":        download_url,
                "filename":   filename,
                "size_bytes": size_bytes,
                "size_human": _human_size(size_bytes),
                "local_path": KIWIX_DIR / filename,
            }

    return books


# ── Download ──────────────────────────────────────────────────────────────────

def download_zim(book, progress_cb=None):
    """
    Download a ZIM archive, resuming automatically if partially complete.

    progress_cb(bytes_done, total_bytes) is called after each 1 MB chunk.
    Returns the local Path to the completed file.
    """
    KIWIX_DIR.mkdir(parents=True, exist_ok=True)
    dest  = book["local_path"]
    url   = book["url"]
    total = book["size_bytes"]

    existing = dest.stat().st_size if dest.exists() else 0
    if existing and existing == total:
        return dest  # already fully downloaded

    headers = {"Range": f"bytes={existing}-"} if existing else {}

    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        mode = "ab" if existing else "wb"
        done = existing
        with open(dest, mode) as f:
            for chunk in r.iter_content(chunk_size=1 << 20):  # 1 MB
                f.write(chunk)
                done += len(chunk)
                if progress_cb:
                    progress_cb(done, total)

    return dest


# ── ZIM article extraction ────────────────────────────────────────────────────

def _html_to_text(html_bytes):
    """Strip HTML and return clean plain text."""
    soup = BeautifulSoup(html_bytes, "html.parser")
    for tag in soup(["script", "style", "sup", "figure", "nav",
                     "footer", "aside", "table"]):
        tag.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _iter_archive(archive):
    """Yield non-redirect entries from a libzim Archive."""
    total = getattr(archive, "all_entry_count", None) \
            or getattr(archive, "entry_count", 0)
    for i in range(total):
        try:
            entry = archive._get_entry_by_id(i)
            if not entry.is_redirect:
                yield entry
        except Exception:
            continue


def iter_zim_documents(zim_path, min_chars=300):
    """
    Yield (source_name, text) pairs extracted from a ZIM archive.

    Skips redirects, images, CSS/JS, and very short articles.
    source_name format:  kiwix:<zim-stem>:<article-title>
    """
    if not HAS_LIBZIM:
        raise RuntimeError(
            "libzim is required to read ZIM files. "
            "Install it with:  pip install libzim"
        )

    zim_path = Path(zim_path)
    # Use the stable base name as the source prefix, not the dated filename
    stem = _base_name(zim_path.stem) if re.search(r"_\d{4}-\d{2}$", zim_path.stem) \
           else zim_path.stem

    archive = Archive(str(zim_path))
    yielded = 0
    skipped = 0

    for entry in _iter_archive(archive):
        try:
            item = entry.get_item()
            if "html" not in item.mimetype.lower():
                continue

            text = _html_to_text(bytes(item.content))
            if len(text) < min_chars:
                skipped += 1
                continue

            yield f"kiwix:{stem}:{entry.title}", text
            yielded += 1

        except Exception:
            continue

    print(f"  {yielded} articles extracted from {zim_path.name} "
          f"({skipped} too short, skipped)")
