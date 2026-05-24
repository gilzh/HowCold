"""Scrape all bookshelf recipes from EatYourBooks, excluding Good Food Magazine."""
import json
import os
import re
import time

import browser_cookie3
from curl_cffi import requests
from bs4 import BeautifulSoup

COOKIES_FILE = "/Users/gilles/Coding/FoodPlanner/eatyourbooks_cookies.json"
SAVED_RECIPES_FILE = "/Users/gilles/Coding/FoodPlanner/saved_recipes.json"
SAVED_RECIPES_DETAILED_FILE = "/Users/gilles/Coding/FoodPlanner/saved_recipes_detailed.json"
INGREDIENTS_CACHE_FILE = "/Users/gilles/Coding/FoodPlanner/ingredients_cache.json"
BASE_URL = "https://www.eatyourbooks.com"
BOOKSHELF_URL = f"{BASE_URL}/bookshelf"
EXCLUDE_SOURCE = "good food magazine"


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def make_session():
    session = requests.Session(impersonate="chrome120")
    try:
        cj = browser_cookie3.chrome(domain_name="eatyourbooks.com")
        for c in cj:
            session.cookies.set(c.name, c.value, domain=c.domain)
        cookies = [
            {"name": c.name, "value": c.value, "domain": c.domain,
             "path": c.path, "sameSite": "None"}
            for c in cj
        ]
        save_json(COOKIES_FILE, cookies)
        print(f"Loaded {len(cookies)} cookies from Chrome.")
    except Exception as e:
        print(f"Could not read Chrome cookies: {e}. Falling back to saved cookies.")
        saved = load_json(COOKIES_FILE, [])
        for c in saved:
            session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
    return session


def parse_page(soup):
    """Parse recipe items from a bookshelf page. Returns (recipes, skipped_count)."""
    recipes = []
    skipped = 0

    for li in soup.select("li.listing.recipe"):
        recipe_id = li.get("data-id", "")
        if not recipe_id:
            continue

        # Name and URL
        title_a = li.select_one("a.RecipeTitleExp")
        if not title_a:
            continue
        name = title_a.get_text(strip=True)
        href = title_a.get("href", "")
        url = BASE_URL + href if href.startswith("/") else href

        # Source book — use full-title anchor
        source_a = li.select_one("a.RecipeBookTitleExp.full-title") or li.select_one("a.RecipeBookTitleExp")
        source_book = source_a.get_text(strip=True) if source_a else ""

        # Exclude Good Food Magazine
        if EXCLUDE_SOURCE in source_book.lower():
            skipped += 1
            continue

        # Categories and ingredients from the meta list
        meta_lis = li.select("ul.meta li")
        categories = []
        ingredients = []
        for meta_li in meta_lis:
            text = meta_li.get_text(strip=True)
            if text.startswith("Categories:"):
                raw = text[len("Categories:"):].strip()
                categories = [c.strip() for c in raw.split(";") if c.strip()]
            elif text.startswith("Ingredients:"):
                raw = text[len("Ingredients:"):].strip()
                ingredients = [i.strip() for i in raw.split(";") if i.strip()]

        cache_key = f"eyb_{recipe_id}"
        recipes.append({
            "normalized": {
                "id": cache_key,
                "name": name,
                "url": url,
                "rating": None,
                "rating_count": None,
                "time": None,
                "difficulty": None,
                "attributes": categories,
                "source": "eatyourbooks",
                "source_book": source_book,
            },
            "ingredients": ingredients,
        })

    return recipes, skipped


def get_total_pages(soup):
    page_links = soup.select(".pages a")
    max_page = 1
    for a in page_links:
        try:
            n = int(a.get_text(strip=True))
            if n > max_page:
                max_page = n
        except ValueError:
            pass
    return max_page


def main():
    existing_simple = load_json(SAVED_RECIPES_FILE, [])
    existing_detailed = load_json(SAVED_RECIPES_DETAILED_FILE, [])
    ingredients_cache = load_json(INGREDIENTS_CACHE_FILE, {})

    non_eyb_simple = [r for r in existing_simple if r.get("source") != "eatyourbooks"]
    non_eyb_detailed = [r for r in existing_detailed if r.get("source") != "eatyourbooks"]
    print(f"Keeping {len(non_eyb_simple)} non-EatYourBooks recipes. Re-scraping EatYourBooks bookshelf...")

    session = make_session()

    # Fetch page 1 to get total page count
    print(f"Fetching page 1...")
    r = session.get(BOOKSHELF_URL, timeout=15)
    if r.status_code != 200:
        print(f"Failed: HTTP {r.status_code}")
        return
    if "sign-in" in r.url or "login" in r.url.lower():
        print("Not authenticated. Log in to EatYourBooks in Chrome and retry.")
        return

    soup = BeautifulSoup(r.text, "html.parser")
    total_pages = get_total_pages(soup)
    print(f"Total pages: {total_pages}")

    new_recipes = []
    seen_ids = set()
    total_skipped = 0

    def process_page(soup, page_num):
        nonlocal total_skipped
        recipes, skipped = parse_page(soup)
        total_skipped += skipped
        added = 0
        for item in recipes:
            rid = item["normalized"]["id"]
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            new_recipes.append(item)
            ingredients_cache[rid] = item["ingredients"]
            added += 1
        return added, skipped

    added, skipped = process_page(soup, 1)
    print(f"  Page 1: +{added} recipes, skipped {skipped} (Good Food Magazine)")

    for page in range(2, total_pages + 1):
        url = f"{BOOKSHELF_URL}/{page}"
        try:
            r = session.get(url, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print(f"  Page {page}: error — {e}")
            time.sleep(2)
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        added, skipped = process_page(soup, page)

        if page % 25 == 0 or page == total_pages:
            print(f"  Page {page}/{total_pages}: +{added} | total so far: {len(new_recipes)} | skipped GFM: {total_skipped}")

        time.sleep(0.3)

    print(f"\nDone. {len(new_recipes)} EatYourBooks recipes scraped, {total_skipped} Good Food Magazine recipes excluded.")

    new_simple = [r["normalized"] for r in new_recipes]
    new_detailed = [{**r["normalized"], "details": {"ingredients": r["ingredients"]}} for r in new_recipes]

    updated_simple = non_eyb_simple + new_simple
    updated_detailed = non_eyb_detailed + new_detailed

    save_json(SAVED_RECIPES_FILE, updated_simple)
    print(f"Updated {SAVED_RECIPES_FILE} ({len(updated_simple)} total)")

    save_json(SAVED_RECIPES_DETAILED_FILE, updated_detailed)
    print(f"Updated {SAVED_RECIPES_DETAILED_FILE} ({len(updated_detailed)} total)")

    save_json(INGREDIENTS_CACHE_FILE, ingredients_cache)
    print(f"Updated {INGREDIENTS_CACHE_FILE}")


if __name__ == "__main__":
    main()
