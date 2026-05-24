"""Inspect BBC Good Food saved items page structure."""
import json
import re
from playwright.sync_api import sync_playwright

COOKIES_FILE = "/Users/gilles/Coding/FoodPlanner/bbcgoodfood_cookies.json"
URL = "https://www.bbcgoodfood.com/user/4188931/saved-items"

def fix_cookies(cookies):
    valid_same_site = {"Strict", "Lax", "None"}
    for cookie in cookies:
        if "sameSite" not in cookie or cookie["sameSite"] not in valid_same_site:
            cookie["sameSite"] = "None"
    return cookies

with open(COOKIES_FILE) as f:
    saved_cookies = json.load(f)

json_responses = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.add_cookies(fix_cookies(saved_cookies))
    page = context.new_page()

    def on_response(response):
        ct = response.headers.get("content-type", "")
        if "json" in ct:
            try:
                data = response.json()
                json_responses.append((response.url, data))
            except Exception:
                pass

    page.on("response", on_response)
    page.goto(URL)
    page.wait_for_timeout(4000)

    # Count recipe links
    links = page.query_selector_all("a[href*='/recipes/'], a[href*='/premium/']")
    ids = set()
    for l in links:
        href = l.get_attribute("href") or ""
        m = re.search(r"/(recipes|premium)/([^/?#]+)", href)
        if m:
            ids.add(href)
    print(f"Recipe links on page load: {len(ids)}")

    # Check for pagination
    print("\nPagination elements:")
    for sel in ["[aria-label*='page'], .pagination, nav[aria-label*='Page'], [data-page]",
                "button:has-text('Load more')", "a[rel='next']",
                "[class*='pagination']", "[class*='Pagination']"]:
        try:
            els = page.query_selector_all(sel)
            for el in els:
                print(f"  {sel!r}: {el.inner_text().strip()[:80]!r} | href={el.get_attribute('href')}")
        except Exception:
            pass

    # Check total count
    print("\nCount indicators:")
    for sel in ["[data-total]", ".save-count", "[class*='count']", "[class*='total']",
                "h1", "h2", ".page-title"]:
        try:
            els = page.query_selector_all(sel)
            for el in els:
                t = el.inner_text().strip()
                if t and len(t) < 100:
                    print(f"  {sel!r}: {t!r}")
        except Exception:
            pass

    # JSON responses with recipe-like data
    print(f"\nJSON responses captured: {len(json_responses)}")
    for url, data in json_responses[:5]:
        print(f"  {url}")
        if isinstance(data, dict):
            print(f"    keys: {list(data.keys())[:10]}")

    # Scroll and check
    print("\nScrolling 5x with End key...")
    for _ in range(5):
        page.keyboard.press("End")
        page.wait_for_timeout(2000)

    links2 = page.query_selector_all("a[href*='/recipes/'], a[href*='/premium/']")
    ids2 = set()
    for l in links2:
        href = l.get_attribute("href") or ""
        m = re.search(r"/(recipes|premium)/([^/?#]+)", href)
        if m:
            ids2.add(href)
    print(f"Recipe links after 5 scrolls: {len(ids2)}")

    print(f"\nCurrent URL: {page.url}")

    browser.close()

print("\nJSON responses with recipe data:")
for url, data in json_responses:
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for k in ("items", "results", "data", "recipes", "savedItems"):
            if isinstance(data.get(k), list):
                items = data[k]
                break
    if items and isinstance(items[0], dict) and ("title" in items[0] or "name" in items[0]):
        print(f"  {url} -> {len(items)} items, keys: {list(items[0].keys())[:8]}")
