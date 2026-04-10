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
    "Anaphylaxis",
    "Stroke",
    "Myocardial_infarction",
    "Sepsis",
    "Snakebite",
    "Frostbite",
    "Altitude_sickness",
    "Drowning",
    "Sprain",
    "Dislocation_of_joint",
    "Childbirth",
    "Tooth_abscess",
    "Eye_injury",
    "Chest_injury",
    "Wound_infection",
]

SURVIVAL_WIKI_PAGES = [
    "Wilderness_survival",
    "Survival_skills",
    "Bushcraft",
    "Water_purification",
    "Fire_making",
    "Navigation",
    "Foraging",
    "Food_preservation",
    "Hunting",
    "Trapping",
    "Rainwater_harvesting",
    "Solar_still",
    "Primitive_technology",
    "Edible_plant",
    "Emergency_management",
    "Food_storage",
    "Knot",
    "Compass",
    "Shelter_(building_and_construction)",
    "Rope",
]

def _fetch_page(title):
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
    return text or None


def iter_medical_wikipedia_documents():
    for title in MEDICAL_WIKI_PAGES:
        try:
            text = _fetch_page(title)
        except Exception as exc:
            print(f"Error fetching Wikipedia page {title}: {exc}")
            continue

        if text:
            yield f"wikipedia:{title}", text


def iter_survival_wikipedia_documents():
    for title in SURVIVAL_WIKI_PAGES:
        try:
            text = _fetch_page(title)
        except Exception as exc:
            print(f"Error fetching Wikipedia page {title}: {exc}")
            continue

        if text:
            yield f"wikipedia:{title}", text
