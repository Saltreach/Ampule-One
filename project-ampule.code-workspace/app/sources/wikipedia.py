import requests

MEDICAL_WIKI_PAGES = [
    # Core first aid
    "First_aid",
    "Cardiopulmonary_resuscitation",
    "Triage",
    "Wilderness_first_aid",
    "Tourniquet",
    "Splint_(medicine)",

    # Bleeding and circulation
    "Hemorrhage",
    "Shock_(circulatory)",
    "Wound",
    "Wound_infection",
    "Chest_injury",

    # Trauma
    "Fracture",
    "Sprain",
    "Dislocation_of_joint",
    "Eye_injury",
    "Burn",

    # Environmental
    "Hypothermia",
    "Frostbite",
    "Trench_foot",
    "Heat_stroke",
    "Heat_exhaustion",
    "Dehydration",
    "Altitude_sickness",
    "Sunburn",

    # Waterborne and infectious
    "Diarrhea",
    "Foodborne_illness",
    "Cholera",
    "Dysentery",
    "Giardia",
    "Wound_infection",

    # Vector and animal-borne
    "Lyme_disease",
    "Malaria",
    "Rabies",
    "Tetanus",
    "Snakebite",

    # Emergencies
    "Anaphylaxis",
    "Stroke",
    "Myocardial_infarction",
    "Sepsis",
    "Appendicitis",
    "Abdominal_pain",
    "Drowning",
    "Childbirth",

    # Dental and minor
    "Tooth_abscess",
    "Poisoning",
]

SURVIVAL_WIKI_PAGES = [
    # Foundations
    "Wilderness_survival",
    "Survival_skills",
    "Bushcraft",
    "Primitive_technology",
    "Emergency_management",

    # Water
    "Water_purification",
    "Rainwater_harvesting",
    "Solar_still",
    "Water_well",

    # Fire
    "Fire_making",
    "Bow_drill",
    "Ferrocerium",
    "Flint",
    "Tinder_(flammable_material)",

    # Shelter
    "Debris_hut",
    "Snow_shelter",
    "Bivouac_shelter",
    "Lean-to",

    # Navigation
    "Navigation",
    "Compass",
    "Celestial_navigation",
    "Dead_reckoning",
    "Natural_navigation",
    "Map",

    # Signalling and rescue
    "Signal_mirror",
    "Personal_locator_beacon",
    "Distress_signal",

    # Food procurement
    "Foraging",
    "Edible_plant",
    "Poisonous_plant",
    "Medicinal_plant",
    "Hunting",
    "Trapping",
    "Deadfall_trap",
    "Snare_(device)",
    "Fishing",

    # Food and water storage
    "Food_preservation",
    "Food_storage",
    "Smoking_(cooking)",
    "Canning",
    "Fermentation_in_food_processing",

    # Tools and cordage
    "Knot",
    "Rope",
    "Paracord",
    "Axe",
    "Knife",
    "Flint_knapping",

    # Environment-specific
    "Desert_survival",
    "Arctic_survival",
    "Maritime_survival_techniques",
    "Urban_survival",

    # Long-term / extended
    "Permaculture",
    "Seed_saving",
    "Herbal_medicine",
    "Root_cellar",

    # Hazards
    "Nuclear_fallout",
    "Pandemic_preparedness",
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
    # -1 is the Wikipedia API's sentinel for "page not found"
    if page.get("pageid") == -1:
        return None

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
        else:
            print(f"Skipped (not found): wikipedia:{title}")


def iter_survival_wikipedia_documents():
    for title in SURVIVAL_WIKI_PAGES:
        try:
            text = _fetch_page(title)
        except Exception as exc:
            print(f"Error fetching Wikipedia page {title}: {exc}")
            continue

        if text:
            yield f"wikipedia:{title}", text
        else:
            print(f"Skipped (not found): wikipedia:{title}")
