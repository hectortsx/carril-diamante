"""Browser release check: every page at phone and desktop width, in real Chrome.

Usage:
  python3 -m http.server 8765 --bind 127.0.0.1 --directory site   (in another terminal)
  python3 scripts/browser_check.py [base_url] [shots_dir]

For each page and viewport it:
  - enforces the production CSP (infra/security-headers.json) and records violations
  - scrolls like a visitor (so lazy images and reveals fire), then takes a full-page screenshot
  - runs axe-core (WCAG 2.0/2.1/2.2 A + AA rules) and lists violations
  - checks horizontal overflow, console errors, failed requests, a playing hero video
Exit code 1 if anything fails.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765").rstrip("/")
SHOTS = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "shots"
SHOTS.mkdir(parents=True, exist_ok=True)
CSP = json.loads((ROOT / "infra" / "security-headers.json").read_text())["Content-Security-Policy"]
CSP = CSP.replace("; upgrade-insecure-requests", "")  # local server is plain http
AXE = (ROOT / "scripts" / "vendor" / "axe.min.js").read_text()

PAGES = ["/", "/en/", "/privacidad/", "/en/privacy/", "/accesibilidad/", "/en/accessibility/", "/404.html"]
VIEWS = {"desktop": (1440, 900), "mobile": (390, 844)}

failures = []


def check(page_path, view, browser):
    w, h = VIEWS[view]
    ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
    page = ctx.new_page()
    errors, failed, csp = [], [], []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("requestfailed", lambda r: failed.append(r.url))

    def add_csp(route):
        if route.request.resource_type != "document":
            route.continue_()  # leave media/range requests alone
            return
        resp = route.fetch()
        headers = dict(resp.headers)
        if headers.get("content-type", "").startswith("text/html"):
            headers["content-security-policy"] = CSP
        route.fulfill(response=resp, headers=headers)

    page.route("**/*", add_csp)
    page.add_init_script("document.addEventListener('securitypolicyviolation', e => "
                         "(window.__csp = window.__csp || []).push(e.violatedDirective + ' ' + e.blockedURI))")
    resp = page.goto(BASE + page_path, wait_until="networkidle")
    status = resp.status if resp else 0
    # scroll like a visitor
    height = page.evaluate("document.documentElement.scrollHeight")
    for y in range(0, height, int(h * 0.6)):
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(120)
    page.wait_for_timeout(900)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1800)
    name = page_path.strip("/").replace("/", "_").replace(".html", "") or "home"
    page.screenshot(path=str(SHOTS / f"{name}-{view}.png"), full_page=True)

    info = page.evaluate("""() => ({
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      csp: window.__csp || [],
      h1: document.querySelectorAll('h1').length,
      video: [...document.querySelectorAll('video')].map(v => ({ready: v.readyState, paused: v.paused, err: v.error && v.error.code}))
    })""")
    page.evaluate(AXE)
    axe = page.evaluate("""async () => {
      const r = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
      return r.violations.map(v => ({id: v.id, impact: v.impact, n: v.nodes.length, sample: v.nodes[0].target.join(' ')}));
    }""")
    # mobile menu must cover the screen even after scrolling (a blurred/transformed header breaks this)
    menu_h = None
    if page.is_visible("[data-menu-open]"):
        page.evaluate("window.scrollTo(0, 1200)")
        page.wait_for_timeout(400)
        page.click("[data-menu-open]")
        page.wait_for_timeout(500)
        menu_h = page.evaluate("document.querySelector('[data-menu]').getBoundingClientRect().height")
    ctx.close()

    expect_status = 404 if page_path == "/404.html" else 200
    problems = []
    if status != expect_status and page_path != "/404.html":
        problems.append(f"HTTP {status}")
    if info["overflow"]:
        problems.append("horizontal overflow")
    if info["h1"] != 1:
        problems.append(f"{info['h1']} h1 elements")
    if info["csp"]:
        problems.append(f"CSP violations: {info['csp']}")
    if errors:
        problems.append(f"console errors: {errors[:3]}")
    if failed:
        problems.append(f"failed requests: {failed[:3]}")
    for v in info["video"]:
        if v["err"] or v["paused"]:
            problems.append(f"hero video not playing: {v}")
    if menu_h is not None and menu_h < h - 1:
        problems.append(f"open menu is {menu_h:.0f}px tall after scrolling, not full screen ({h}px)")
    for v in axe:
        problems.append(f"axe {v['impact']}: {v['id']} x{v['n']} e.g. {v['sample']}")
    flag = "FAIL" if problems else "ok"
    print(f"[{flag}] {page_path} {view}")
    for p in problems:
        print("      -", p)
        failures.append(f"{page_path} {view}: {p}")


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="chrome")  # real Chrome: plays H.264 video like visitors' browsers
    for p in PAGES:
        for v in VIEWS:
            check(p, v, browser)
    browser.close()

print(f"\n{len(failures)} problem(s). Screenshots: {SHOTS}")
sys.exit(1 if failures else 0)
