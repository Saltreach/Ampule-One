import requests

MEDICAL_WIKI_PAGES = [
    "First_aid",
    "Cardiopulmonary_resuscitation",
    "Hemorrhage",
    "Dehydration",
    "Hypothermia",
    "Burn",
    "Fracture",
    "Shock_(circulatory)",
    "Heat_stroke",
    "Wound",
]

def fetch_wikipedia_page(title):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": 1,
        "redirects": 1,
        "titles": title,
    }
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return None

    pages = r.json().get("query", {}).get("pages", {})
    if not pages:
        return None

    page = next(iter(pages.values()))
    text = page.get("extract", "").strip()
    return text

def iter_medical_wikipedia_documents():
    for title in MEDICAL_WIKI_PAGES:
        try:
            text = fetch_wikipedia_page(title)
        except Exception as exc:
            print(f"Error fetching Wikipedia page {title}: {exc}")
            continue

        if text:
            yield f"wikipedia:{title}", text
