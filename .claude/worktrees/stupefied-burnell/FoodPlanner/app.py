import json
import os
import random
import re
import threading

import requests
from curl_cffi import requests as cf_requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

RECIPES_FILE = "/Users/gilles/Coding/FoodPlanner/saved_recipes.json"
PLANTOEAT_COOKIES_FILE = "/Users/gilles/Coding/FoodPlanner/plantoeat_cookies.json"
EATYOURBOOKS_COOKIES_FILE = "/Users/gilles/Coding/FoodPlanner/eatyourbooks_cookies.json"
INGREDIENTS_CACHE_FILE = "/Users/gilles/Coding/FoodPlanner/ingredients_cache.json"
MEAL_PLAN_FILE = "/Users/gilles/Coding/FoodPlanner/meal_plan.json"
PAGE_SIZE = 10

FISH_KEYWORDS = {
    "salmon", "tuna", "cod", "haddock", "halibut", "trout", "sardine",
    "mackerel", "anchov", "anchovy", "anchovies", "prawn", "shrimp",
    "seafood", "crab", "lobster", "mussel", "clam", "scallop", "squid",
    "octopus", "tilapia", "sea bass", "plaice", "monkfish", "sole",
    "herring", "kipper", "smoked fish", "fish fillet", "fish pie",
    "fish cake", "fishcake", "kedgeree", "whitebait",
}
RED_MEAT_KEYWORDS = {
    "beef", "pork", "veal", "duck", "lamb", "bacon", "ham", "sausage",
    "mince", "steak", "venison", "chorizo", "pancetta", "lardons",
    "meatball", "minced meat", "ground beef", "ground pork", "rabbit",
    "pheasant", "partridge", "grouse", "goose", "quail", "offal",
    "liver", "kidney", "black pudding", "salami", "pepperoni",
    "prosciutto", "bresaola", "mortadella",
}
WHITE_MEAT_KEYWORDS = {
    "chicken", "turkey",
}
DESSERT_ATTR_KEYWORDS = {
    "dessert", "cake", "cheesecake", "biscuit", "cookie", "ice cream",
    "frozen dessert", "mousse", "trifle", "custard", "candy", "sweet bread",
}
DESSERT_NAME_KEYWORDS = {
    "cake", "brownie", "tart", "cheesecake", "mousse", "ice cream", "crumble",
    "muffin", "cupcake", "biscuit", "cookie", "fudge", "tiramisu", "pavlova",
    "sorbet", "meringue", "panna cotta", "pudding", "dessert", "gelato",
    "macaron", "éclair", "eclair", "profiterole", "baklava", "halva",
    "doughnut", "donut",
}

_cache_lock = threading.Lock()
_recipes_mtime = None


def load_recipes():
    with open(RECIPES_FILE) as f:
        return json.load(f)


def maybe_reload_recipes():
    global ALL_RECIPES, INGREDIENT_INDEX, _recipes_mtime, INGREDIENTS_CACHE, _cache_mtime
    recipes_mtime = os.path.getmtime(RECIPES_FILE)
    if recipes_mtime != _recipes_mtime:
        _recipes_mtime = recipes_mtime
        ALL_RECIPES = load_recipes()
    cache_mtime = os.path.getmtime(INGREDIENTS_CACHE_FILE) if os.path.exists(INGREDIENTS_CACHE_FILE) else 0
    if cache_mtime != _cache_mtime:
        _cache_mtime = cache_mtime
        INGREDIENTS_CACHE = load_ingredients_cache()
    INGREDIENT_INDEX = build_ingredient_index()


def load_ingredients_cache():
    if os.path.exists(INGREDIENTS_CACHE_FILE):
        with open(INGREDIENTS_CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_ingredients_cache(cache):
    with open(INGREDIENTS_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def load_meal_plan():
    if os.path.exists(MEAL_PLAN_FILE):
        with open(MEAL_PLAN_FILE) as f:
            return json.load(f)
    return []


def save_meal_plan(plan):
    with open(MEAL_PLAN_FILE, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)


DIET_ICONS = {"vegetarian": "🥦", "fish": "🐟", "red_meat": "🥩", "white_meat": "🍗", "dessert": "🍰"}
def _favicon(url):
    return f'<img src="{url}" width="16" height="16" style="vertical-align:middle;margin-left:4px">'

SOURCE_ICONS = {
    "bbcgoodfood":  _favicon("https://www.bbcgoodfood.com/favicon.ico"),
    "plantoeat":    '<img src="/static/icons/icon_PlanToEat.png" width="16" height="16" style="vertical-align:middle;margin-left:4px">',
    "eatyourbooks": '<img src="/static/icons/icon_EatYourBooks.png" width="16" height="16" style="vertical-align:middle;margin-left:4px">',
}

# Ordered list: first match wins. More specific phrases must come before shorter keywords.
INGREDIENT_EMOJIS = [
    ("olive oil",       "🫒"), ("soy sauce",       "🫙"), ("fish sauce",      "🫙"),
    ("pine nut",        "🌰"), ("sunflower seed",   "🌻"), ("pumpkin seed",    "🌻"),
    ("kidney bean",     "🫘"), ("black bean",       "🫘"), ("cannellini",      "🫘"),
    ("chickpea",        "🫘"), ("lentil",           "🫘"),
    ("ground beef",     "🥩"), ("minced beef",      "🥩"), ("minced pork",     "🥩"),
    ("chicken",         "🍗"), ("turkey",           "🍗"),
    ("salmon",          "🐟"), ("tuna",             "🐟"), ("cod",             "🐟"),
    ("haddock",         "🐟"), ("trout",            "🐟"), ("mackerel",        "🐟"),
    ("sardine",         "🐟"), ("anchov",           "🐟"), ("herring",         "🐟"),
    ("prawn",           "🦐"), ("shrimp",           "🦐"),
    ("crab",            "🦀"), ("lobster",          "🦞"),
    ("mussel",          "🦪"), ("scallop",          "🦪"), ("clam",            "🦪"),
    ("squid",           "🦑"), ("octopus",          "🦑"),
    ("fish",            "🐟"),
    ("beef",            "🥩"), ("pork",             "🥩"), ("lamb",            "🥩"),
    ("veal",            "🥩"), ("duck",             "🥩"), ("venison",         "🥩"),
    ("bacon",           "🥓"), ("ham",              "🥓"), ("pancetta",        "🥓"),
    ("chorizo",         "🌭"), ("sausage",          "🌭"), ("salami",          "🌭"),
    ("meatball",        "🥩"), ("mince",            "🥩"), ("steak",           "🥩"),
    ("egg",             "🥚"),
    ("milk",            "🥛"), ("cream",            "🥛"), ("yogurt",          "🥛"),
    ("yoghurt",         "🥛"), ("butter",           "🧈"),
    ("parmesan",        "🧀"), ("cheddar",          "🧀"), ("mozzarella",      "🧀"),
    ("feta",            "🧀"), ("brie",             "🧀"), ("goat",            "🧀"),
    ("cheese",          "🧀"),
    ("garlic",          "🧄"), ("onion",            "🧅"), ("shallot",         "🧅"),
    ("tomato",          "🍅"), ("potato",           "🥔"), ("sweet potato",    "🍠"),
    ("carrot",          "🥕"), ("broccoli",         "🥦"), ("cauliflower",     "🥦"),
    ("spinach",         "🥬"), ("kale",             "🥬"), ("lettuce",         "🥬"),
    ("cabbage",         "🥬"), ("leek",             "🥬"), ("chard",           "🥬"),
    ("aubergine",       "🍆"), ("eggplant",         "🍆"),
    ("courgette",       "🥒"), ("zucchini",         "🥒"), ("cucumber",        "🥒"),
    ("pepper",          "🫑"), ("capsicum",         "🫑"),
    ("chilli",          "🌶️"), ("chili",            "🌶️"), ("paprika",         "🌶️"),
    ("mushroom",        "🍄"), ("corn",             "🌽"), ("asparagus",       "🌿"),
    ("avocado",         "🥑"), ("pea",              "🫛"), ("bean",            "🫘"),
    ("celery",          "🌿"), ("fennel",           "🌿"), ("artichoke",       "🌿"),
    ("beetroot",        "🫚"), ("turnip",           "🌿"), ("parsnip",         "🌿"),
    ("radish",          "🌿"),
    ("lemon",           "🍋"), ("lime",             "🍋"), ("orange",          "🍊"),
    ("apple",           "🍎"), ("pear",             "🍐"), ("banana",          "🍌"),
    ("mango",           "🥭"), ("pineapple",        "🍍"), ("coconut",         "🥥"),
    ("grape",           "🍇"), ("strawberry",       "🍓"), ("blueberry",       "🫐"),
    ("raspberry",       "🍓"), ("cherry",           "🍒"), ("peach",           "🍑"),
    ("plum",            "🍑"), ("fig",              "🍈"), ("pomegranate",     "🍊"),
    ("almond",          "🥜"), ("cashew",           "🥜"), ("walnut",          "🥜"),
    ("peanut",          "🥜"), ("pistachio",        "🥜"), ("hazelnut",        "🌰"),
    ("sesame",          "🌰"),
    ("pasta",           "🍝"), ("spaghetti",        "🍝"), ("penne",           "🍝"),
    ("noodle",          "🍜"), ("rice",             "🍚"), ("bread",           "🍞"),
    ("flour",           "🌾"), ("oat",              "🌾"), ("quinoa",          "🌾"),
    ("honey",           "🍯"), ("sugar",            "🍬"), ("salt",            "🧂"),
    ("oil",             "🫙"), ("vinegar",          "🫙"), ("stock",           "🫙"),
    ("broth",           "🫙"), ("sauce",            "🫙"), ("tahini",          "🫙"),
    ("mustard",         "🫙"), ("mayo",             "🫙"),
    ("basil",           "🌿"), ("thyme",            "🌿"), ("rosemary",        "🌿"),
    ("oregano",         "🌿"), ("parsley",          "🌿"), ("coriander",       "🌿"),
    ("cilantro",        "🌿"), ("mint",             "🌿"), ("dill",            "🌿"),
    ("sage",            "🌿"), ("tarragon",         "🌿"), ("bay leaf",        "🌿"),
    ("cumin",           "🌿"), ("turmeric",         "🌿"), ("cinnamon",        "🌿"),
    ("ginger",          "🫚"), ("nutmeg",           "🌿"), ("cardamom",        "🌿"),
    ("vanilla",         "🌿"), ("curry",            "🌿"),
    ("chocolate",       "🍫"), ("cocoa",            "🍫"),
    ("wine",            "🍷"), ("beer",             "🍺"),
    ("water",           "💧"),
]


def ingredient_emoji(text):
    lower = text.lower()
    for keyword, emoji in INGREDIENT_EMOJIS:
        if keyword in lower:
            return emoji
    return "·"


def build_shopping_list(results):
    """Collect, deduplicate, and alphabetically sort all ingredients from the menu."""
    seen = set()
    items = []
    for r in results:
        for ing in INGREDIENTS_CACHE.get(r["id"], []):
            key = ing.strip().lower()
            if key and key not in seen:
                seen.add(key)
                items.append((ing.strip(), ingredient_emoji(ing)))
    items.sort(key=lambda x: x[0].lower())
    return items


def parse_rating(recipe):
    """Extract numeric rating float from rating text, e.g. 'A star rating of 4.15 out of 5.' -> 4.15"""
    rating_text = recipe.get("rating") or ""
    m = re.search(r"(\d+(?:\.\d+)?)\s+out of", rating_text)
    return float(m.group(1)) if m else None


def classify_diet(recipe):
    """Return 'dessert', 'vegetarian', 'fish', 'red_meat', 'white_meat', or None."""
    attrs = " ".join(recipe.get("attributes", [])).lower()
    name = recipe.get("name", "").lower()

    # Dessert: check attributes first, then name as fallback
    if any(kw in attrs for kw in DESSERT_ATTR_KEYWORDS):
        return "dessert"
    if not attrs and any(kw in name for kw in DESSERT_NAME_KEYWORDS):
        return "dessert"

    # Vegetarian/vegan: trust category tags directly
    if "vegetarian" in attrs or "vegan" in attrs:
        return "vegetarian"

    # For fish/meat use ingredients from cache
    ingredients_text = " ".join(INGREDIENTS_CACHE.get(recipe["id"], [])).lower()
    if not ingredients_text:
        return None

    if any(kw in ingredients_text for kw in FISH_KEYWORDS):
        return "fish"
    if any(kw in ingredients_text for kw in RED_MEAT_KEYWORDS):
        return "red_meat"
    if any(kw in ingredients_text for kw in WHITE_MEAT_KEYWORDS):
        return "white_meat"

    # PlanToEat recipes that have ingredients but no meat/fish detected → vegetarian
    if recipe.get("source") == "plantoeat":
        return "vegetarian"
    return None


ALL_RECIPES = load_recipes()
_recipes_mtime = os.path.getmtime(RECIPES_FILE)
INGREDIENTS_CACHE = load_ingredients_cache()
_cache_mtime = os.path.getmtime(INGREDIENTS_CACHE_FILE) if os.path.exists(INGREDIENTS_CACHE_FILE) else 0

# Build a search index: recipe_id -> lowercase ingredient text (from cache)
def build_ingredient_index():
    return {
        rid: " ".join(ings).lower()
        for rid, ings in INGREDIENTS_CACHE.items()
        if ings
    }

INGREDIENT_INDEX = build_ingredient_index()


def plantoeat_session():
    session = requests.Session()
    if os.path.exists(PLANTOEAT_COOKIES_FILE):
        with open(PLANTOEAT_COOKIES_FILE) as f:
            cookies = json.load(f)
        for c in cookies:
            session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return session


def fetch_bbc_ingredients(url):
    try:
        r = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        soup = BeautifulSoup(r.text, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = next((d for d in data if d.get("@type") == "Recipe"), None)
                if data and data.get("@type") == "Recipe":
                    ings = data.get("recipeIngredient", [])
                    if ings:
                        return sorted(ings)
            except Exception:
                pass
        ings = []
        for el in soup.select("[class*='ingredient'], [data-ingredient]"):
            text = el.get_text(strip=True)
            if text and text not in ings:
                ings.append(text)
        return sorted(ings) if ings else None
    except Exception:
        return None


def fetch_plantoeat_ingredients(url, recipe_id):
    try:
        session = plantoeat_session()
        api_url = f"https://app.plantoeat.com/recipes/{recipe_id}.json"
        r = session.get(api_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            ingredients = []
            for section in data.get("recipe_ingredients", []) or []:
                for ing in section.get("ingredients", []) or []:
                    parts = []
                    if ing.get("quantity"):
                        parts.append(ing["quantity"])
                    if ing.get("unit"):
                        parts.append(ing["unit"])
                    if ing.get("ingredient"):
                        parts.append(ing["ingredient"])
                    if ing.get("preparation"):
                        parts.append(f"({ing['preparation']})")
                    text = " ".join(parts).strip()
                    if text:
                        ingredients.append(text)
            if ingredients:
                return ingredients
        r = session.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        ings = []
        for el in soup.select("[class*='ingredient'], li"):
            text = el.get_text(strip=True)
            if text and len(text) < 200 and text not in ings:
                ings.append(text)
        return ings[:50] if ings else None
    except Exception:
        return None


def eatyourbooks_session():
    session = cf_requests.Session(impersonate="chrome120")
    if os.path.exists(EATYOURBOOKS_COOKIES_FILE):
        with open(EATYOURBOOKS_COOKIES_FILE) as f:
            cookies = json.load(f)
        for c in cookies:
            session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
    return session


def fetch_eatyourbooks_ingredients(url):
    try:
        session = eatyourbooks_session()
        r = session.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        ing_list = soup.select("ul.list.ingredients li")
        if ing_list:
            return [li.get_text(strip=True) for li in ing_list if li.get_text(strip=True)]
        return None
    except Exception:
        return None


def parse_minutes(time_str):
    if not time_str:
        return None
    time_str = time_str.lower()
    total = 0
    m = re.search(r"(\d+)\s*hr", time_str)
    if m:
        total += int(m.group(1)) * 60
    m = re.search(r"(\d+)\s*min", time_str)
    if m:
        total += int(m.group(1))
    return total if total else None


def get_recipe_time(recipe):
    if recipe.get("time"):
        t = parse_minutes(recipe["time"])
        if t:
            return t
    for attr in recipe.get("attributes", []):
        t = parse_minutes(attr)
        if t:
            return t
    return None


@app.route("/api/ingredients")
def api_ingredients():
    recipe_id = request.args.get("id", "").strip()
    url = request.args.get("url", "").strip()
    source = request.args.get("source", "").strip()

    if not recipe_id:
        return jsonify({"error": "missing id"}), 400

    with _cache_lock:
        if recipe_id in INGREDIENTS_CACHE:
            return jsonify({"ingredients": INGREDIENTS_CACHE[recipe_id]})

    ingredients = None
    if source == "plantoeat":
        ingredients = fetch_plantoeat_ingredients(url, recipe_id)
    elif source == "eatyourbooks":
        ingredients = fetch_eatyourbooks_ingredients(url)
    else:
        ingredients = fetch_bbc_ingredients(url)

    if ingredients is None:
        ingredients = []

    with _cache_lock:
        INGREDIENTS_CACHE[recipe_id] = ingredients
        INGREDIENT_INDEX[recipe_id] = " ".join(ingredients).lower()
        save_ingredients_cache(INGREDIENTS_CACHE)

    return jsonify({"ingredients": ingredients})


MENU_PLAN = [
    ("fish", 2),
    ("red_meat", 1),
    ("white_meat", 2),
    ("vegetarian", 2),
]


def build_suggested_menu(source_filter=""):
    """Pick recipes according to MENU_PLAN, randomly, without repetition."""
    maybe_reload_recipes()
    by_diet = {}
    for recipe in ALL_RECIPES:
        if source_filter and recipe.get("source", "bbcgoodfood") != source_filter:
            continue
        diet = classify_diet(recipe)
        if diet not in by_diet:
            by_diet[diet] = []
        by_diet[diet].append(recipe)
    for lst in by_diet.values():
        random.shuffle(lst)

    results = []
    for diet, count in MENU_PLAN:
        pool = by_diet.get(diet, [])
        results.extend(pool[:count])
    return results


@app.route("/")
def index():
    maybe_reload_recipes()
    search_filter = request.args.get("search", "").strip().lower()
    difficulty_filter = request.args.get("difficulty", "").strip().lower()
    max_time_str = request.args.get("max_time", "").strip()
    source_filter = request.args.get("source", "").strip()
    diet_filter = request.args.get("diet", "").strip().lower()
    suggest = request.args.get("suggest", "")
    page = max(1, int(request.args.get("page", "1") or "1"))

    if suggest:
        meal_plan_ids = set(load_meal_plan())
        results = []
        for r in build_suggested_menu(source_filter):
            r = dict(r)
            r["diet_type"] = classify_diet(r)
            r["diet_icon"] = DIET_ICONS.get(r["diet_type"], "")
            r["source_icon"] = SOURCE_ICONS.get(r.get("source", "bbcgoodfood"), SOURCE_ICONS["bbcgoodfood"])
            r["rating_value"] = parse_rating(r)
            r["in_menu"] = r["id"] in meal_plan_ids
            results.append(r)
        total = len(results)
        shopping_list = build_shopping_list(results)
        return render_template("plan.html", results=results, page=1,
                               total_pages=1, total=total, page_base="/?suggest=1&",
                               menu_count=len(meal_plan_ids), suggest=True,
                               shopping_list=shopping_list)

    if not request.args:
        return render_template("plan.html", results=None, page=1, total_pages=1,
                               total=0, query_args={})

    max_time = None
    if max_time_str:
        try:
            max_time = int(max_time_str)
        except ValueError:
            pass

    search_keywords = search_filter.split()

    candidates = []
    for recipe in ALL_RECIPES:
        if search_keywords:
            ing_text = INGREDIENT_INDEX.get(str(recipe["id"]), "")
            haystack = recipe["name"].lower() + " " + " ".join(recipe.get("attributes", [])).lower() + " " + ing_text
            if not all(kw in haystack for kw in search_keywords):
                continue

        if source_filter and recipe.get("source", "bbcgoodfood") != source_filter:
            continue

        if difficulty_filter:
            attrs_lower = [a.lower() for a in recipe.get("attributes", [])]
            diff = recipe.get("difficulty", "") or ""
            if difficulty_filter not in attrs_lower and difficulty_filter not in diff.lower():
                continue

        if max_time is not None:
            t = get_recipe_time(recipe)
            if t is not None and t > max_time:
                continue

        if diet_filter:
            if classify_diet(recipe) != diet_filter:
                continue

        candidates.append(recipe)

    random.shuffle(candidates)
    total = len(candidates)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, total_pages)
    start = (page - 1) * PAGE_SIZE
    results = candidates[start:start + PAGE_SIZE]

    from urllib.parse import urlencode
    base_args = {k: v for k, v in request.args.items() if k != "page"}
    base_qs = urlencode(base_args)
    page_base = f"/?{base_qs}&" if base_qs else "/?"

    meal_plan_ids = set(load_meal_plan())
    for r in results:
        r["diet_type"] = classify_diet(r)
        r["diet_icon"] = DIET_ICONS.get(r["diet_type"], "")
        r["source_icon"] = SOURCE_ICONS.get(r.get("source", "bbcgoodfood"), SOURCE_ICONS["bbcgoodfood"])
        r["rating_value"] = parse_rating(r)
        r["in_menu"] = r["id"] in meal_plan_ids

    return render_template("plan.html", results=results, page=page,
                           total_pages=total_pages, total=total, page_base=page_base,
                           menu_count=len(meal_plan_ids))


@app.route("/menu")
def menu():
    plan_ids = load_meal_plan()
    recipe_map = {r["id"]: r for r in ALL_RECIPES}
    plan_recipes = []
    for rid in plan_ids:
        r = recipe_map.get(rid)
        if r:
            r = dict(r)
            r["diet_type"] = classify_diet(r)
            r["diet_icon"] = DIET_ICONS.get(r["diet_type"], "")
            r["source_icon"] = SOURCE_ICONS.get(r.get("source", "bbcgoodfood"), SOURCE_ICONS["bbcgoodfood"])
            r["rating_value"] = parse_rating(r)
            plan_recipes.append(r)
    return render_template("menu.html", recipes=plan_recipes)


@app.route("/api/menu/toggle", methods=["POST"])
def menu_toggle():
    data = request.get_json()
    recipe_id = (data or {}).get("id", "").strip()
    if not recipe_id:
        return jsonify({"error": "missing id"}), 400
    plan = load_meal_plan()
    if recipe_id in plan:
        plan.remove(recipe_id)
        in_menu = False
    else:
        plan.append(recipe_id)
        in_menu = True
    save_meal_plan(plan)
    return jsonify({"in_menu": in_menu, "count": len(plan)})


def _pte_session():
    """curl_cffi session with PTE cookies loaded."""
    session = cf_requests.Session(impersonate="chrome120")
    if os.path.exists(PLANTOEAT_COOKIES_FILE):
        with open(PLANTOEAT_COOKIES_FILE) as f:
            cookies = json.load(f)
        for c in cookies:
            if "plantoeat.com" in c.get("domain", ""):
                session.cookies.set(c["name"], c["value"], domain=c["domain"].lstrip("."))
    return session


def _pte_create_recipe(session, name, source_url):
    """Create a minimal PTE recipe and return its rid, or raise on failure."""
    # GET /recipes/new – PTE creates a draft and embeds its id in the page
    r = session.get("https://app.plantoeat.com/recipes/new", timeout=15)
    match = re.search(r'data-recipe-id="(\d+)"', r.text)
    if not match:
        raise RuntimeError("Could not find recipe id in /recipes/new response")
    rid = match.group(1)
    # Fill in the recipe title and source URL
    session.post(
        f"https://app.plantoeat.com/recipes/update/{rid}",
        data={
            "recipe[title]": name,
            "recipe[source]": source_url,
            "recipe[servings]": "1",
        },
        timeout=15,
    )
    return rid


@app.route("/api/schedule_to_pte", methods=["POST"])
def schedule_to_pte():
    data = request.get_json() or {}
    rid      = str(data.get("rid", "")).strip()
    name     = str(data.get("name", "")).strip()
    url      = str(data.get("url", "")).strip()
    date     = str(data.get("date", "")).strip()
    section  = str(data.get("section", "dinner")).strip()

    if not date:
        return jsonify({"error": "Missing date"}), 400
    if not rid and not (name and url):
        return jsonify({"error": "Provide either rid (PTE) or name+url (external)"}), 400

    try:
        session = _pte_session()
        if not rid:
            # BBC GF / EYB: create a stub recipe in PTE first
            rid = _pte_create_recipe(session, name, url)
        resp = session.post(
            "https://app.plantoeat.com/planner/create",
            data={"rid": rid, "date": date, "section": section},
            timeout=15,
        )
        if resp.status_code == 200:
            return jsonify({"ok": True, "rid": rid})
        return jsonify({"error": f"PlanToEat returned {resp.status_code}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5050)
