"""Scrape all BBC Good Food saved recipes via cursor-based API and update saved_recipes files."""
import json
import os
import re
from playwright.sync_api import sync_playwright

COOKIES_FILE = "/Users/gilles/Coding/FoodPlanner/bbcgoodfood_cookies.json"
SAVED_RECIPES_FILE = "/Users/gilles/Coding/FoodPlanner/saved_recipes.json"
SAVED_RECIPES_DETAILED_FILE = "/Users/gilles/Coding/FoodPlanner/saved_recipes_detailed.json"
USER_ID = "4188931"
BASE_URL = "https://www.bbcgoodfood.com"
API_URL = f"{BASE_URL}/api/my-hub/user/{USER_ID}/saved-items?limit=30"


def fix_cookies(cookies):
    valid_same_site = {"Strict", "Lax", "None"}
    for cookie in cookies:
        if "sameSite" not in cookie or cookie["sameSite"] not in valid_same_site:
            cookie["sameSite"] = "None"
    return cookies


def load_existing_recipes(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def recipe_url_from_entity(entity):
    """entity format: 'recipes~slug' or 'premium~slug'"""
    if not entity:
        return ""
    parts = entity.split("~", 1)
    if len(parts) == 2:
        return f"{BASE_URL}/{parts[0]}/{parts[1]}"
    return f"{BASE_URL}/{entity}"


def normalize_recipe(item, content_map_entry):
    """Build a normalized recipe from an API item + its savedItemContentMap entry."""
    client_id = str(content_map_entry.get("clientId", "") or item.get("id", "") or "")
    title = item.get("title", "")

    # URL is directly on the item
    url = item.get("url") or recipe_url_from_entity(content_map_entry.get("entity", ""))
    if not url and client_id:
        url = f"{BASE_URL}/recipes/{client_id}"

    # Rating is in item.rating (not theme)
    rating_obj = item.get("rating") or {}
    if not isinstance(rating_obj, dict):
        rating_obj = {}
    rating = rating_obj.get("ratingValue")
    rating_count = rating_obj.get("ratingCount")
    rating_str = f"A star rating of {rating} out of 5." if rating else None
    rating_count_str = f"{rating_count} ratings" if rating_count is not None else None

    # Attributes come from item.terms: [{"slug": "time", "display": "50 mins"}, ...]
    terms = item.get("terms") or []
    attributes = [t["display"] for t in terms if isinstance(t, dict) and t.get("display")]

    difficulty = next(
        (t["display"] for t in terms if isinstance(t, dict) and t.get("slug") == "skillLevel"),
        None,
    )
    time_str = next(
        (t["display"] for t in terms if isinstance(t, dict) and t.get("slug") == "time"),
        None,
    )

    return {
        "id": client_id,
        "name": title,
        "url": url,
        "rating": rating_str,
        "rating_count": rating_count_str,
        "time": time_str,
        "difficulty": difficulty,
        "attributes": attributes,
    }


def main():
    with open(COOKIES_FILE) as f:
        cookies = fix_cookies(json.load(f))

    existing_simple = load_existing_recipes(SAVED_RECIPES_FILE)
    existing_detailed = load_existing_recipes(SAVED_RECIPES_DETAILED_FILE)

    # Remove old BBC Good Food entries and replace them all
    non_bbc_simple = [r for r in existing_simple if r.get("source") == "plantoeat"]
    non_bbc_detailed = [r for r in existing_detailed if r.get("source") == "plantoeat"]
    print(f"Keeping {len(non_bbc_simple)} Plan to Eat recipes. Re-scraping BBC Good Food...")

    all_raw = []  # list of (item, content_map_entry)
    seen_ids = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(cookies)
        req = context.request

        next_url = API_URL
        page_num = 1

        while next_url:
            print(f"  Page {page_num}: {next_url[:80]}...")
            response = req.get(next_url)

            if response.status != 200:
                print(f"  HTTP {response.status} — stopping.")
                break

            data = response.json()
            items = data.get("items", [])
            content_map = data.get("savedItemContentMap", [])
            next_url = data.get("nextUrl") or None
            total = data.get("totalItems", "?")

            new_on_page = 0
            for item, cmap in zip(items, content_map):
                uid = str(cmap.get("clientId", "") or item.get("id", ""))
                if not uid or uid in seen_ids:
                    continue
                seen_ids.add(uid)
                all_raw.append((item, cmap))
                new_on_page += 1

            print(f"    +{new_on_page} (total so far: {len(all_raw)} / {total})")

            if not items:
                break

            page_num += 1

        browser.close()

    print(f"\nTotal BBC Good Food recipes scraped: {len(all_raw)}")

    new_simple = []
    new_detailed = []
    for item, cmap in all_raw:
        normalized = normalize_recipe(item, cmap)
        if not normalized["id"] or not normalized["name"]:
            continue
        new_simple.append(normalized)
        new_detailed.append({**normalized, "details": {"item": item, "contentMap": cmap}})

    updated_simple = non_bbc_simple + new_simple
    updated_detailed = non_bbc_detailed + new_detailed

    with open(SAVED_RECIPES_FILE, "w") as f:
        json.dump(updated_simple, f, indent=2, ensure_ascii=False)
    print(f"Updated {SAVED_RECIPES_FILE} ({len(updated_simple)} total)")

    with open(SAVED_RECIPES_DETAILED_FILE, "w") as f:
        json.dump(updated_detailed, f, indent=2, ensure_ascii=False)
    print(f"Updated {SAVED_RECIPES_DETAILED_FILE} ({len(updated_detailed)} total)")


if __name__ == "__main__":
    main()
