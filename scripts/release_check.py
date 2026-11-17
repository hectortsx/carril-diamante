"""Static release check: run before every upload.  python3 -I scripts/release_check.py

Fails (exit 1) on:
  - any item still listed in src/content/site.json "unconfirmed" (owner hasn't confirmed it)
  - [OWNER: / [COUNSEL: text in any public file
  - per page: missing lang, title, description, canonical, og:image, skip link; not exactly one <main> and one <h1>
  - inline <script> (other than JSON-LD), inline event handlers, style="" attributes
  - local links/assets that don't exist in site/
  - files that must never ship (.env, .map, .DS_Store, test pages)
Then run scripts/browser_check.py for axe, CSP, overflow and video.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "site"
problems = []

site = json.loads((ROOT / "src" / "content" / "site.json").read_text())
for item in site.get("unconfirmed", []):
    problems.append(f"owner must confirm: {item}")

for f in SITE_DIR.rglob("*"):
    if f.is_file() and f.suffix in {".html", ".txt", ".xml", ".css", ".js"}:
        text = f.read_text(errors="ignore")
        if "[OWNER:" in text or "[COUNSEL:" in text:
            problems.append(f"{f.relative_to(SITE_DIR)}: unresolved [OWNER:/[COUNSEL: placeholder")
    if f.is_file() and (f.name in {".DS_Store", ".env"} or f.suffix == ".map" or "test" in f.stem.lower()):
        problems.append(f"{f.relative_to(SITE_DIR)}: must not ship")


def exists(url_path):
    p = url_path.split("?")[0].split("#")[0]
    if not p or p == "/":
        return (SITE_DIR / "index.html").exists()
    target = SITE_DIR / p.lstrip("/")
    return target.is_file() or (target / "index.html").is_file()


for page in sorted(SITE_DIR.rglob("*.html")):
    rel = page.relative_to(SITE_DIR)
    html = page.read_text()
    checks = {
        "lang attribute": re.search(r'<html lang="(es|en)"', html),
        "title": re.search(r"<title>[^<]{10,}</title>", html),
        "meta description": re.search(r'<meta name="description" content="[^"]{30,}"', html),
        "canonical": re.search(r'<link rel="canonical" href="https://', html),
        "og:image": 'property="og:image"' in html,
        "skip link": 'class="skip-link" href="#main"' in html,
    }
    for name, ok in checks.items():
        if not ok:
            problems.append(f"{rel}: missing {name}")
    if html.count("<main") != 1:
        problems.append(f"{rel}: {html.count('<main')} <main> elements")
    if len(re.findall(r"<h1[\s>]", html)) != 1:
        problems.append(f"{rel}: not exactly one <h1>")
    for m in re.finditer(r"<script(?![^>]*\bsrc=)([^>]*)>", html):
        if "application/ld+json" not in m.group(1):
            problems.append(f"{rel}: inline <script>")
    if re.search(r"\son[a-z]+\s*=", html):
        problems.append(f"{rel}: inline event handler")
    if re.search(r'\sstyle\s*=\s*"', html):
        problems.append(f"{rel}: style attribute")
    for m in re.finditer(r'(?:href|src)="([^"]+)"|srcset="([^"]+)"', html):
        urls = [m.group(1)] if m.group(1) else [u.strip().split(" ")[0] for u in m.group(2).split(",")]
        for u in urls:
            parsed = urlparse(u)
            if parsed.scheme or u.startswith(("#", "mailto:", "tel:")):
                continue
            if not exists(u):
                problems.append(f"{rel}: broken local link {u}")

for p in problems:
    print("FAIL", p)
print(f"\n{len(problems)} problem(s)" if problems else "release check passed")
sys.exit(1 if problems else 0)
