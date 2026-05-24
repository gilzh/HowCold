"""Pre-fetch and cache ingredients for all BBC Good Food recipes missing from the cache."""
import json
import os
import time

import requests
from bs4 import BeautifulSoup

RECIPES_FILE = "/Users/gilles/Coding/FoodPlanner/saved_recipes.json"
INGREDIENTS_CACHE_FILE = "/Users/gilles/Coding/FoodPlanner/ingredients_cache.json"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_bbc_ingredients(url):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": USER_AGENT})
        soup = BeautifulSoup(r.text, "html.parser")
        # Try JSON-LD first (most reliable)
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
        # Fallback: scrape ingredient elements
        ings = []
        for el in soup.select("[class*='ingredient'], [data-ingredient]"):
            text = el.get_text(strip=True)
            if text and text not in ings:
                ings.append(text)
        return sorted(ings) if ings else []
    except Exception as e:
        print(f"    Error: {e}")
        return None


def main():
    recipes = load_json(RECIPES_FILE, [])
    cache = load_json(INGREDIENTS_CACHE_FILE, {})

    bbc_recipes = [r for r in recipes if r.get("source", "bbcgoodfood") == "bbcgoodfood"]
    missing = [r for r in bbc_recipes if r["id"] not in cache]

    print(f"BBC Good Food recipes: {len(bbc_recipes)}")
    print(f"Already cached: {len(bbc_recipes) - len(missing)}")
    print(f"To fetch: {len(missing)}")

    if not missing:
        print("All BBC ingredients already cached.")
        return

    fetched = 0
    failed = 0
    for i, recipe in enumerate(missing):
        print(f"  [{i+1}/{len(missing)}] {recipe['name']} ...", end=" ", flush=True)
        ings = fetch_bbc_ingredients(recipe["url"])
        if ings is None:
            print(f"FAILED")
            cache[recipe["id"]] = []
            failed += 1
        else:
            cache[recipe["id"]] = ings
            print(f"{len(ings)} ingredients")
            fetched += 1

        # Save incrementally every 20 recipes
        if (i + 1) % 20 == 0:
            save_json(INGREDIENTS_CACHE_FILE, cache)
            print(f"  [saved checkpoint at {i+1}]")

        time.sleep(0.5)

    save_json(INGREDIENTS_CACHE_FILE, cache)
    print(f"\nDone. Fetched: {fetched}, failed/empty: {failed}")


if __name__ == "__main__":
    main()
