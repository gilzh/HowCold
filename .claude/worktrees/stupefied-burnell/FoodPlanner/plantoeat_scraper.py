"""
PlanToEat ingredient fetcher.
- Keeps the existing 1242 PlanToEat recipe list in saved_recipes.json
- Fetches each recipe's full data from /api/v1/recipes/{id} to get ingredients with amounts
- Updates ingredients_cache.json
"""
import json
import os
import sys
import time

from curl_cffi import requests as cffi_requests

BASE_URL = "https://app.plantoeat.com"
COOKIES_FILE = "/Users/gilles/Coding/FoodPlanner/plantoeat_cookies.json"
SAVED_RECIPES_FILE = "/Users/gilles/Coding/FoodPlanner/saved_recipes.json"
INGREDIENTS_CACHE_FILE = "/Users/gilles/Coding/FoodPlanner/ingredients_cache.json"


def log(msg):
    print(msg, flush=True)


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def make_session():
    raw_cookies = load_json(COOKIES_FILE, [])
    session = cffi_requests.Session(impersonate="chrome120")
    for c in raw_cookies:
        if "plantoeat.com" in c.get("domain", ""):
            session.cookies.set(c["name"], c["value"], domain=c["domain"].lstrip("."))
    return session


def extract_ingredients(r):
    """Return ingredient strings with amounts, e.g. '2 medium aubergines'."""
    ings = r.get("ingredients") or []
    if ings:
        result = []
        for ing in ings:
            parts = []
            amt = (str(ing.get("amount") or "")).strip()
            unit = (ing.get("unit") or "").strip()
            title = (ing.get("title") or "").strip()
            note = (ing.get("note") or "").strip()
            if amt and amt != "0":
                parts.append(amt)
            if unit:
                parts.append(unit)
            if title:
                parts.append(title)
            if note:
                parts.append(f"({note})")
            if title:
                result.append(" ".join(parts))
        if result:
            return result
    # Fallback: ingredient_titles (names only)
    titles = r.get("ingredient_titles") or []
    return [t.strip() for t in titles if t.strip()]


def main():
    log("Loading session cookies...")
    session = make_session()

    log("Loading existing recipes and cache...")
    all_recipes = load_json(SAVED_RECIPES_FILE, [])
    cache = load_json(INGREDIENTS_CACHE_FILE, {})

    pte_recipes = [r for r in all_recipes if r.get("source") == "plantoeat"]
    log(f"Found {len(pte_recipes)} PlanToEat recipes to update.")

    # Clear stale PTE cache entries
    for rid in [str(r["id"]) for r in pte_recipes]:
        cache.pop(rid, None)

    updated = 0
    errors = 0
    checkpoint_every = 50

    for i, recipe in enumerate(pte_recipes):
        rid = str(recipe["id"])
        url = f"{BASE_URL}/api/v1/recipes/{rid}"
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code != 200:
                log(f"  [{i+1}/{len(pte_recipes)}] ERROR {resp.status_code} for id={rid}")
                errors += 1
                continue
            data = resp.json()
            ings = extract_ingredients(data)
            if ings:
                cache[rid] = ings
                updated += 1
            # Also fix the recipe name if it was garbled
            api_title = (data.get("title") or "").strip()
            if api_title and set(api_title) <= {"*", " "}:
                log(f"  [{i+1}] BAD name id={rid}: {api_title!r}")
            elif api_title and api_title != recipe.get("name", ""):
                recipe["name"] = api_title

        except Exception as e:
            log(f"  [{i+1}/{len(pte_recipes)}] EXCEPTION id={rid}: {e}")
            errors += 1

        if (i + 1) % 10 == 0:
            log(f"  Progress: {i+1}/{len(pte_recipes)} — {updated} with ingredients, {errors} errors")

        if (i + 1) % checkpoint_every == 0:
            save_json(INGREDIENTS_CACHE_FILE, cache)
            save_json(SAVED_RECIPES_FILE, all_recipes)
            log(f"  Checkpoint saved at {i+1}.")

        time.sleep(0.05)

    # Final save
    save_json(INGREDIENTS_CACHE_FILE, cache)
    save_json(SAVED_RECIPES_FILE, all_recipes)
    log(f"\nDone. {updated}/{len(pte_recipes)} recipes got ingredients. {errors} errors.")
    log(f"Cache now has {len(cache)} entries.")


if __name__ == "__main__":
    main()
