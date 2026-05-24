"""Dump the BBC Good Food API response to understand pagination."""
import json
from playwright.sync_api import sync_playwright

COOKIES_FILE = "/Users/gilles/Coding/FoodPlanner/bbcgoodfood_cookies.json"
USER_ID = "4188931"
BASE_URL = "https://www.bbcgoodfood.com"
API_URL = f"{BASE_URL}/api/my-hub/user/{USER_ID}/saved-items"

def fix_cookies(cookies):
    valid_same_site = {"Strict", "Lax", "None"}
    for cookie in cookies:
        if "sameSite" not in cookie or cookie["sameSite"] not in valid_same_site:
            cookie["sameSite"] = "None"
    return cookies

with open(COOKIES_FILE) as f:
    cookies = fix_cookies(json.load(f))

all_captured = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    context.add_cookies(cookies)

    def on_response(response):
        if "saved-items" in response.url:
            try:
                data = response.json()
                all_captured.append((response.url, data))
            except Exception:
                pass

    page = context.new_page()
    page.on("response", on_response)
    page.goto(f"{BASE_URL}/user/{USER_ID}/saved-items")
    page.wait_for_timeout(5000)

    # Also try direct API calls with different params
    req = context.request
    for params in ["?limit=30", "?limit=30&offset=30", "?limit=30&page=2",
                   "?limit=30&cursor=30", "?limit=100", "?limit=300"]:
        r = req.get(API_URL + params)
        try:
            data = r.json()
            if isinstance(data, list):
                print(f"\n{params}: list of {len(data)}")
                if data:
                    print(f"  first item keys: {list(data[0].keys())}")
                    print(f"  first item id: {data[0].get('id')}, title: {data[0].get('title')}")
                    print(f"  last item id: {data[-1].get('id')}, title: {data[-1].get('title')}")
            elif isinstance(data, dict):
                print(f"\n{params}: dict keys={list(data.keys())}")
                # Print top-level non-list values
                for k, v in data.items():
                    if not isinstance(v, (list, dict)):
                        print(f"  {k}: {v!r}")
                # Print list lengths
                for k, v in data.items():
                    if isinstance(v, list):
                        print(f"  {k}: list of {len(v)}")
                        if v and isinstance(v[0], dict):
                            print(f"    first item keys: {list(v[0].keys())[:8]}")
        except Exception as e:
            print(f"\n{params}: error {e}")

    browser.close()

print("\n\nPage-load API captures:")
for url, data in all_captured:
    print(f"\n  URL: {url}")
    if isinstance(data, list):
        print(f"  list of {len(data)}, first id={data[0].get('id') if data else None}")
    elif isinstance(data, dict):
        print(f"  dict keys: {list(data.keys())}")
        for k, v in data.items():
            if not isinstance(v, (list, dict)):
                print(f"    {k}: {v!r}")
            elif isinstance(v, list):
                print(f"    {k}: list[{len(v)}]")
