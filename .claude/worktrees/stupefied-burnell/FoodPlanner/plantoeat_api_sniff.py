"""
Sniff Plan to Eat planner API calls.
Opens the planner with saved cookies and logs all XHR/fetch requests.
Interact with the planner manually (drag a recipe onto a day) to capture
the scheduling endpoint and payload.
Press Ctrl+C or close the browser when done.
"""
import json
from playwright.sync_api import sync_playwright

COOKIES_FILE = "/Users/gilles/Coding/FoodPlanner/plantoeat_cookies.json"
BASE_URL = "https://app.plantoeat.com"


def fix_cookies(cookies):
    for c in cookies:
        if c.get("sameSite") not in {"Strict", "Lax", "None"}:
            c["sameSite"] = "None"
    return cookies


with open(COOKIES_FILE) as f:
    saved_cookies = json.load(f)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.add_cookies(fix_cookies(saved_cookies))
    page = context.new_page()

    # Intercept all requests
    def on_request(req):
        if req.resource_type in ("xhr", "fetch"):
            print(f"\n>>> {req.method} {req.url}")
            body = req.post_data
            if body:
                print(f"    BODY: {body[:500]}")

    def on_response(resp):
        if resp.request.resource_type in ("xhr", "fetch"):
            status = resp.status
            url = resp.url
            if status >= 400 or any(kw in url for kw in ["plan", "schedule", "meal", "recipe"]):
                try:
                    body = resp.text()
                    print(f"<<< {status} {url}")
                    print(f"    RESPONSE: {body[:300]}")
                except Exception:
                    pass

    page.on("request", on_request)
    page.on("response", on_response)

    print("Loading planner...")
    page.goto(f"{BASE_URL}/planner")
    page.wait_for_timeout(4000)

    print("\n" + "="*60)
    print("Planner loaded. Now:")
    print("  1. Drag a recipe from the recipe list onto a day slot")
    print("  2. Watch the terminal for the API call")
    print("  3. Close the browser window when done")
    print("="*60 + "\n")

    # Keep browser open until closed manually
    try:
        page.wait_for_event("close", timeout=300_000)
    except Exception:
        pass

    browser.close()

print("\nDone.")
