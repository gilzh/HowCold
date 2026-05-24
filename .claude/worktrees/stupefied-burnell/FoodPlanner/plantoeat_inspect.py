"""One-shot inspector: dumps page structure info to understand Plan to Eat's recipe layout."""
import json
import os
import re
from playwright.sync_api import sync_playwright

COOKIES_FILE = "/Users/gilles/Coding/FoodPlanner/plantoeat_cookies.json"
BASE_URL = "https://app.plantoeat.com"


def fix_cookies(cookies):
    valid_same_site = {"Strict", "Lax", "None"}
    for cookie in cookies:
        if "sameSite" not in cookie or cookie["sameSite"] not in valid_same_site:
            cookie["sameSite"] = "None"
    return cookies


with open(COOKIES_FILE) as f:
    saved_cookies = json.load(f)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.add_cookies(fix_cookies(saved_cookies))
    page = context.new_page()
    page.goto(f"{BASE_URL}/recipes")
    page.wait_for_timeout(4000)

    # 1. Look for embedded JSON in <script> tags
    scripts = page.query_selector_all("script:not([src])")
    for i, s in enumerate(scripts):
        content = s.inner_text()
        if "recipe" in content.lower() and len(content) > 200:
            print(f"\n=== script[{i}] (first 500 chars) ===")
            print(content[:500])

    # 2. Look for total count indicators
    for sel in [
        ".total", ".count", "[data-total]", "[data-count]",
        ".pagination", "nav[aria-label*='page']", ".page-count",
        ".recipes-count", ".recipe-count",
    ]:
        els = page.query_selector_all(sel)
        for el in els:
            try:
                text = el.inner_text().strip()
                if text:
                    print(f"\n[{sel}] => {text[:200]!r}")
            except Exception:
                pass

    # 3. Count recipe links
    links = page.query_selector_all("a[href*='/recipes/']")
    ids = set()
    for l in links:
        href = l.get_attribute("href") or ""
        m = re.search(r"/recipes/(\d+)", href)
        if m:
            ids.add(m.group(1))
    print(f"\nRecipe links found in DOM: {len(ids)}")

    # 4. Check for pagination links
    print("\nPagination links:")
    for sel in ["a[href*='page=']", "a[rel='next']", ".pagination a", "[aria-label='Next page']"]:
        els = page.query_selector_all(sel)
        for el in els:
            href = el.get_attribute("href") or ""
            text = el.inner_text().strip()
            print(f"  {sel}: {text!r} -> {href}")

    # 5. Try scrolling and check if more recipes appear
    print("\nScrolling to check for lazy load...")
    for _ in range(5):
        page.keyboard.press("End")
        page.wait_for_timeout(2000)

    links2 = page.query_selector_all("a[href*='/recipes/']")
    ids2 = set()
    for l in links2:
        href = l.get_attribute("href") or ""
        m = re.search(r"/recipes/(\d+)", href)
        if m:
            ids2.add(m.group(1))
    print(f"Recipe links after scrolling: {len(ids2)}")

    # 6. Check the URL and page title
    print(f"\nCurrent URL: {page.url}")
    print(f"Page title: {page.title()}")

    # 7. Try navigating to page 2
    page.goto(f"{BASE_URL}/recipes?page=2")
    page.wait_for_timeout(3000)
    links3 = page.query_selector_all("a[href*='/recipes/']")
    ids3 = set()
    for l in links3:
        href = l.get_attribute("href") or ""
        m = re.search(r"/recipes/(\d+)", href)
        if m:
            ids3.add(m.group(1))
    print(f"\nAfter goto ?page=2: URL={page.url}, recipe links={len(ids3)}")
    new_on_p2 = ids3 - ids2
    print(f"  New recipe IDs on page 2: {len(new_on_p2)}")

    browser.close()

print("\nDone.")
