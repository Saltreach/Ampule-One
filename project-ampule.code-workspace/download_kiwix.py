"""
Project Ampule — Kiwix Knowledge Base Downloader

Run this script once (while online) to download an offline knowledge
base from the Kiwix library.  The downloaded ZIM files are stored in
data/kiwix/ and automatically indexed the next time you run:

    python ingest_online.py
    python ingest.py

Usage:
    python download_kiwix.py
"""

import sys

from app.sources.kiwix import PACKS, HAS_LIBZIM, fetch_catalog, download_zim


# ── Progress bar ──────────────────────────────────────────────────────────────

def _progress(done, total, width=45):
    if not total:
        return
    frac  = min(done / total, 1.0)
    full  = int(width * frac)
    bar   = "█" * full + "░" * (width - full)
    done_mb  = done  / 1_048_576
    total_mb = total / 1_048_576
    print(f"\r  [{bar}] {done_mb:6.0f} / {total_mb:.0f} MB",
          end="", flush=True)


# ── Catalog display ───────────────────────────────────────────────────────────

def _show_packs(catalog):
    pack_keys = list(PACKS.keys())
    for idx, key in enumerate(pack_keys, 1):
        pack = PACKS[key]
        print(f"  [{idx}] {pack['label']}")
        print(f"       {pack['description']}")
        for name in pack["books"]:
            book = catalog.get(name)
            if book:
                print(f"         • {book['title']:<50}  {book['size_human']:>9}")
            else:
                print(f"         • {name}  (not in catalog)")
        print()
    return pack_keys


def _show_all_books(catalog):
    book_list = sorted(catalog.values(), key=lambda b: b["title"].lower())
    print(f"\n  {'#':>4}  {'Title':<56}  {'Size':>9}")
    print(f"  {'─'*4}  {'─'*56}  {'─'*9}")
    for i, book in enumerate(book_list, 1):
        print(f"  {i:>4}  {book['title']:<56}  {book['size_human']:>9}")
    return book_list


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print()
    print("  Project Ampule — Knowledge Base Downloader")
    print("  " + "═" * 43)
    print()

    if not HAS_LIBZIM:
        print("  ERROR: libzim is not installed.")
        print("  Install it with:  pip install libzim")
        print()
        sys.exit(1)

    print("  Fetching Kiwix catalog…", end="", flush=True)
    try:
        catalog = fetch_catalog()
    except Exception as exc:
        print(f"\n  Failed to fetch catalog: {exc}")
        sys.exit(1)
    print(f"  {len(catalog)} books available.\n")

    print("  Select a download pack:\n")
    pack_keys = _show_packs(catalog)

    custom_idx = len(pack_keys) + 1
    print(f"  [{custom_idx}] Custom — browse and pick individual books")
    print(f"  [0] Cancel\n")

    try:
        choice = input("  Enter choice: ").strip()
        choice = int(choice)
    except (ValueError, EOFError):
        print("  Cancelled.")
        return

    if choice == 0:
        print("  Cancelled.")
        return

    # Resolve the list of books to download
    if 1 <= choice <= len(pack_keys):
        selected_names = PACKS[pack_keys[choice - 1]]["books"]

    elif choice == custom_idx:
        book_list = _show_all_books(catalog)
        print()
        try:
            raw = input("  Enter numbers separated by spaces: ").strip()
        except EOFError:
            print("  Cancelled.")
            return
        indices = []
        for token in raw.split():
            if token.isdigit():
                i = int(token) - 1
                if 0 <= i < len(book_list):
                    indices.append(i)
        selected_names = [book_list[i]["name"] for i in indices]

    else:
        print("  Invalid choice.")
        return

    books   = [catalog[n] for n in selected_names if n in catalog]
    missing = [n for n in selected_names if n not in catalog]

    if missing:
        print(f"\n  Not found in catalog: {', '.join(missing)}")
    if not books:
        print("  Nothing to download.")
        return

    total_bytes = sum(b["size_bytes"] for b in books)
    print(f"\n  Downloading {len(books)} file(s) — "
          f"{total_bytes / 1_073_741_824:.1f} GB total")
    print("  Saved to: data/kiwix/")
    print("  Downloads resume automatically if interrupted.\n")

    failed = []
    for book in books:
        dest = book["local_path"]
        existing = dest.stat().st_size if dest.exists() else 0
        if existing and existing == book["size_bytes"]:
            print(f"  Already complete: {book['filename']}")
            continue

        print(f"  {book['title']}  ({book['size_human']})")
        try:
            download_zim(book, progress_cb=_progress)
            print(f"\n  Saved: {book['filename']}")
        except KeyboardInterrupt:
            print(f"\n  Interrupted — partial file kept for resume.")
            print("  Re-run this script to continue the download.")
            sys.exit(0)
        except Exception as exc:
            print(f"\n  Failed: {exc}")
            failed.append(book["title"])
        print()

    print()
    if failed:
        print(f"  Completed with errors. Failed: {', '.join(failed)}")
    else:
        print("  All downloads complete.")

    print()
    print("  Next steps:")
    print("    python ingest_online.py   ← indexes ZIM files + online sources")
    print("    python ingest.py          ← builds the search index")
    print()


if __name__ == "__main__":
    main()
