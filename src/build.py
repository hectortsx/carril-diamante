"""Build the static site into site/ from src/content.

Usage:  python3 -I src/build.py

Pages: / (es), /en/, /privacidad/, /en/privacy/, /accesibilidad/, /en/accessibility/, /404.html
Also writes robots.txt, sitemap.xml and .well-known/security.txt.
No inline scripts or style attributes (CSP), except JSON-LD which browsers don't execute.
"""
import datetime as dt
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "src" / "content"
OUT = ROOT / "site"

SITE = json.loads((CONTENT / "site.json").read_text())
LANGS = {code: json.loads((CONTENT / f"{code}.json").read_text()) for code in ("es", "en")}
UPDATED = {"es": "12 de noviembre de 2026", "en": "November 12, 2026"}
TESTED = {
    "es": "Aún no se ha hecho la revisión previa al lanzamiento. Esta sección se completará con la fecha y el método de prueba.",
    "en": "The pre-launch review has not been done yet. This section will list the date and how the site was tested.",
}
GA = SITE["ga_measurement_id"].strip()
V = SITE["asset_version"]

PAIRS = {
    "home": {"es": "/", "en": "/en/"},
    "privacy": {"es": "/privacidad/", "en": "/en/privacy/"},
    "accessibility": {"es": "/accesibilidad/", "en": "/en/accessibility/"},
}

e = html.escape


def a_ext(href, label, t, cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<a{c} href="{e(href)}" target="_blank" rel="noopener">{label}'
            f'<span class="visually-hidden"> {e(t["new_tab"])}</span></a>')


ARROW = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
         '<path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.6" '
         'stroke-linecap="round" stroke-linejoin="round"/></svg>')
ARROW_UP = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<path d="M7 17 17 7M9 7h8v8" fill="none" stroke="currentColor" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round"/></svg>')
PAUSE = ('<svg class="icon icon-pause" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
         '<path d="M9 6v12M15 6v12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
         '<svg class="icon icon-play" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
         '<path d="M8 6l10 6-10 6z" fill="currentColor"/></svg>')
WA_ICON = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" '
           'd="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9'
           '-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3'
           '-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 '
           '0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6a2.7 2.7 0 0 0 1.8-1.2 2.2 2.2 0 0 0 .1-1.2c0-.1-.2-.2-.4-.3z"/></svg>')
PHONE_ICON = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="none" stroke="currentColor" '
              'stroke-width="1.6" stroke-linejoin="round" d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>')
MAIL_ICON = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="none" stroke="currentColor" '
             'stroke-width="1.6" stroke-linejoin="round" d="M3 6h18v12H3zM3 7l9 6 9-6"/></svg>')
BURGER = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 8h16M4 16h16" '
          'stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>')
CLOSE = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6 6 18" '
         'stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>')
FB_ICON = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" '
           'd="M14 8h3V4h-3a4 4 0 0 0-4 4v2H8v4h2v8h4v-8h3l1-4h-4V8z"/></svg>')


def img(name, alt, sizes, cls="", eager=False):
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="/assets/img/{name}-800.webp" '
            f'srcset="/assets/img/{name}-800.webp 800w, /assets/img/{name}-1600.webp 1600w" '
            f'sizes="{sizes}" width="1600" height="900" alt="{e(alt)}" {loading}>')


def head(t, page, title, description, path):
    other = t["other_lang"]
    alts = "".join(
        f'<link rel="alternate" hreflang="{code}" href="{SITE["domain"]}{PAIRS[page][code]}">' for code in ("es", "en"))
    alts += f'<link rel="alternate" hreflang="x-default" href="{SITE["domain"]}{PAIRS[page]["es"]}">'
    ld = ""
    if page == "home":
        data = {
            "@context": "https://schema.org",
            "@type": "SportsActivityLocation",
            "name": SITE["brand"],
            "url": SITE["domain"] + t["home_path"],
            "image": SITE["domain"] + "/og-image.jpg",
            "logo": SITE["domain"] + "/icon-512.png",
            "telephone": SITE["phone_e164"],
            "email": SITE["email"],
            "address": {"@type": "PostalAddress", "addressLocality": "Hudson", "addressRegion": "CO",
                        "postalCode": "80642", "addressCountry": "US"},
            "geo": {"@type": "GeoCoordinates", "latitude": SITE["lat"], "longitude": SITE["lng"]},
            "sameAs": [SITE["facebook"]],
        }
        ld = f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'
    return f"""<!doctype html>
<html lang="{t['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{SITE['domain']}{path}">
{alts}
<meta name="theme-color" content="#0e0d0b">
<meta name="color-scheme" content="dark">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE['brand']}">
<meta property="og:locale" content="{t['locale']}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{SITE['domain']}{path}">
<meta property="og:image" content="{SITE['domain']}/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/archivo-wdth-wght.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/bodoni-moda-wght.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={V}">
<script src="/assets/js/site.js?v={V}" defer></script>
{ld}
</head>
"""


def h2_text(t, key):
    """Plain heading; the gold italic is kept for the hero only, unless a section gives a second part."""
    a, b = t[f"{key}_h2_a"], t.get(f"{key}_h2_b", "")
    # .rise: the heading slides up out of its own bottom edge when its section scrolls in (site.css)
    return '<span class="rise">' + e(a) + (f' <em class="gold-text">{e(b)}</em>' if b else "") + "</span>"


def nav_ids(t):
    return [href[1:] for href, _ in t["nav"]]


def header(t, on_home):
    pre = "" if on_home else t["home_path"]
    links = "".join(f'<li><a href="{pre}{href}">{e(label)}</a></li>' for href, label in t["nav"])
    other = LANGS[t["other_lang"]]
    reg = nav_ids(t)[3]
    return f"""<a class="skip-link" href="#main">{e(t['skip'])}</a>
<header class="site-header" data-header>
  <div class="nav-inner">
    <a class="brand" href="{t['home_path']}" aria-label="{e(t['home_label'])}">
      <img src="/assets/img/logo-carril-480.png" srcset="/assets/img/logo-carril-480.png 480w, /assets/img/logo-carril-960.png 960w" sizes="160px" width="480" height="144" alt="">
    </a>
    <nav class="nav-links" aria-label="{e(t['nav_label'])}"><ul>{links}</ul></nav>
    <div class="nav-actions">
      <a class="lang-link" href="{other['home_path']}" hreflang="{other['lang']}" lang="{other['lang']}"><span aria-hidden="true">{t['other_lang_label']}</span><span class="visually-hidden">{e(t['lang_switch_label'])}</span></a>
      <a class="btn btn-gold btn-sm nav-cta" href="{pre}#{reg}">{e(t['nav_cta'])}</a>
      <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu" data-menu-open>{BURGER}<span class="visually-hidden">{e(t['menu_open'])}</span></button>
    </div>
  </div>
  <div class="menu" id="menu" role="dialog" aria-modal="true" aria-label="{e(t['nav_label'])}" hidden data-menu>
    <button class="menu-close" type="button" data-menu-close>{CLOSE}<span class="visually-hidden">{e(t['menu_close'])}</span></button>
    <ul class="menu-links">{links}</ul>
    <div class="menu-foot">
      <a class="btn btn-gold" href="{pre}#{reg}">{e(t['nav_cta'])}{ARROW}</a>
      <a class="lang-link" href="{other['home_path']}" hreflang="{other['lang']}" lang="{other['lang']}">{e(t['other_lang_name'])}</a>
    </div>
  </div>
</header>
"""


def consent(t):
    if not GA:
        return ""
    return f"""<div class="consent" role="region" aria-labelledby="consent-title" hidden data-consent>
  <p class="consent-title" id="consent-title">{e(t['consent_title'])}</p>
  <p class="consent-body">{e(t['consent_body'])} <a href="{t['privacy_path']}">{e(t['consent_more'])}</a></p>
  <div class="consent-actions">
    <button class="btn btn-ghost" type="button" data-consent-choice="rejected">{e(t['consent_reject'])}</button>
    <button class="btn btn-ghost" type="button" data-consent-choice="granted">{e(t['consent_accept'])}</button>
  </div>
</div>
"""


def footer(t):
    on = t["home_path"]
    links = "".join(f'<li><a href="{on}{href}">{e(label)}</a></li>' for href, label in t["nav"])
    cookie = (f'<li><button class="link-btn" type="button" data-consent-open>{e(t["cookie_settings"])}</button></li>'
              if GA else "")
    return f"""<footer class="site-footer">
  <div class="container footer-grid">
    <div class="footer-brand">
      <img src="/assets/img/logo-carril-480.png" width="480" height="144" alt="{SITE['brand']}" loading="lazy" decoding="async">
      <p>{e(SITE['city'])}</p>
    </div>
    <nav aria-label="{e(t['footer_nav'])}"><p class="footer-h">{e(t['footer_nav'])}</p><ul>{links}</ul></nav>
    <div><p class="footer-h">{e(t['footer_contact'])}</p><ul>
      <li><a href="tel:{SITE['phone_e164']}">{SITE['phone_display']}</a></li>
      <li><a href="mailto:{SITE['email']}">{SITE['email']}</a></li>
      <li>{a_ext(SITE['facebook'], FB_ICON + 'Facebook', t, 'with-icon')}</li>
    </ul></div>
    <div><p class="footer-h">{e(t['footer_legal'])}</p><ul>
      <li><a href="{t['privacy_path']}">{e(t['privacy'])}</a></li>
      <li><a href="{t['accessibility_path']}">{e(t['accessibility'])}</a></li>
      {cookie}
    </ul></div>
  </div>
  <div class="container footer-base"><p>© {SITE['year']} {e(SITE['legal_name'])}. {e(t['rights'])}</p></div>
</footer>
{consent(t)}"""


def body_open(page):
    ga = f' data-ga-id="{e(GA)}"' if GA else ""
    return f'<body class="page-{page}"{ga}>\n'


def home(code):
    t = LANGS[code]
    ids = nav_ids(t)
    races = ""
    for i, r in enumerate(t["races"]):
        sub = f'<p class="race-sub">{e(r["sub"])}</p>' if r.get("sub") else ""
        races += f"""<article class="race reveal" data-delay="{i}">
        <figure class="race-media">{img(r['img'], r['alt'], '(min-width: 900px) 44vw, 100vw')}</figure>
        <div class="race-copy">
          <div><h3 class="race-title">{e(r['title'])}</h3>{sub}<p>{e(r['body'])}</p></div>
        </div>
      </article>"""
    facts = "".join(f'<div class="fact"><dt data-count>{e(v)}</dt><dd>{e(k)}</dd></div>' for v, k in t["facts"])
    items = "".join(
        f'<li class="shot"><img src="/assets/img/{n}-800.webp" srcset="/assets/img/{n}-800.webp 800w, /assets/img/{n}-1600.webp 1600w" sizes="(max-width: 560px) 78vw, (max-width: 1533px) 30vw, 460px" width="800" height="450" alt="{e(alt)}" loading="lazy" decoding="async"></li>'
        for n, alt in t["gallery"])
    dupes = "".join(
        f'<li class="shot"><img src="/assets/img/{n}-800.webp" srcset="/assets/img/{n}-800.webp 800w, /assets/img/{n}-1600.webp 1600w" sizes="(max-width: 560px) 78vw, (max-width: 1533px) 30vw, 460px" width="800" height="450" alt="" loading="lazy" decoding="async"></li>'
        for n, _ in t["gallery"])
    steps = "".join(
        f'<li class="step reveal" data-delay="{i}"><span class="step-n" aria-hidden="true">{i + 1}</span>'
        f'<h3>{e(a)}</h3><p>{e(b)}</p></li>' for i, (a, b) in enumerate(t["steps"]))
    wa = f'https://wa.me/{SITE["whatsapp"]}?text={quote(t["whatsapp_text"])}'
    mail = f'mailto:{SITE["email"]}?subject={quote(t["email_subject"])}'
    maps = f'https://www.google.com/maps/search/?api=1&query={SITE["lat"]}%2C{SITE["lng"]}'
    return head(t, "home", t["title"], t["description"], t["home_path"]) + body_open("home") + header(t, True) + f"""
<main id="main" tabindex="-1">
  <section class="hero" aria-labelledby="hero-title">
    <div class="container hero-copy">
      <p class="eyebrow enter" data-step="0">{e(t['hero_eyebrow'])}</p>
      <h1 class="hero-title" id="hero-title">
        <span class="line"><span class="line-in enter" data-step="1">{e(t['hero_h1_a'])}</span></span>
        <span class="line"><em class="line-in gold-text enter" data-step="2">{e(t['hero_h1_b'])}</em></span>
      </h1>
      <div class="hero-aside enter" data-step="3">
        <p class="lede">{e(t['hero_sub'])}</p>
        <div class="actions">
          <a class="btn btn-gold" href="#{ids[3]}">{e(t['hero_cta'])}{ARROW}</a>
          <a class="btn btn-ghost" href="#{ids[0]}">{e(t['hero_cta2'])}</a>
        </div>
      </div>
    </div>
    <div class="band enter" data-step="2" data-band>
      <video class="band-video" muted playsinline width="1200" height="675" loading="eager" fetchpriority="high" preload="metadata" poster="/assets/img/hero-poster.webp" aria-label="{e(t['video_label'])}" data-hero-video>
        <source src="/assets/video/hero-band.mp4" type="video/mp4">
      </video>
      <div class="band-meta">
        <button class="pill-btn" type="button" aria-pressed="false" data-video-toggle data-label-pause="{e(t['video_pause'])}" data-label-play="{e(t['video_play'])}" hidden>{PAUSE}<span data-label>{e(t['video_pause'])}</span></button>
      </div>
    </div>
  </section>

  <section class="section races" id="{ids[0]}" aria-labelledby="races-title">
    <div class="container">
      <div class="section-head reveal">
        <h2 class="h2" id="races-title">{h2_text(t, 'races')}</h2>
      </div>
      <div class="race-grid">{races}</div>
    </div>
  </section>

  <section class="section track" id="{ids[1]}" aria-labelledby="track-title">
    <div class="container track-grid">
      <figure class="track-media reveal">{img('starting-gate', t['track_img_alt'], '(min-width: 900px) 58vw, 100vw')}</figure>
      <div class="track-copy reveal" data-delay="1">
        <h2 class="h2" id="track-title">{h2_text(t, 'track')}</h2>
        <p class="body">{e(t['track_body'])}</p>
        <dl class="facts">{facts}</dl>
      </div>
    </div>
  </section>

  <section class="section gallery" id="{ids[2]}" aria-labelledby="gallery-title">
    <div class="container gallery-head reveal">
      <div>
        <h2 class="h2" id="gallery-title">{h2_text(t, 'gallery')}</h2>
      </div>
      <button class="pill-btn" type="button" aria-pressed="false" data-marquee-toggle data-label-pause="{e(t['gallery_pause'])}" data-label-play="{e(t['gallery_play'])}" hidden>{PAUSE}<span data-label>{e(t['gallery_pause'])}</span></button>
    </div>
    <div class="marquee" data-marquee tabindex="0" role="region" aria-label="{e(t['gallery_h2_a'])}">
      <div class="marquee-track">
        <ul class="marquee-list">{items}</ul>
        <ul class="marquee-list" aria-hidden="true">{dupes}</ul>
      </div>
    </div>
  </section>

  <section class="section enter-section" id="{ids[3]}" aria-labelledby="reg-title">
    <div class="container">
      <div class="reg-grid">
        <div class="reg-head reveal">
          <h2 class="h2 h2-xl" id="reg-title">{h2_text(t, 'reg')}</h2>
          <p class="body">{e(t['reg_sub'])}</p>
          <p class="fb-dates">{a_ext(SITE['facebook'], FB_ICON + e(t['fb_dates']), t, 'text-link with-icon')}</p>
        </div>
        <ol class="steps">{steps}</ol>
        <div class="contact-row reveal">
          {a_ext(wa, WA_ICON + e(t['btn_whatsapp']), t, 'btn btn-gold btn-lg')}
          <a class="btn btn-ghost btn-lg" href="tel:{SITE['phone_e164']}">{PHONE_ICON}{e(t['btn_call'])} <span class="mono">{SITE['phone_display']}</span></a>
          <a class="btn btn-ghost btn-lg" href="{e(mail)}">{MAIL_ICON}{e(t['btn_email'])}</a>
        </div>
      </div>
      <div class="where reveal">
        <p class="eyebrow">{e(t['where_label'])}</p>
        <p class="where-city">{e(SITE['city'])}</p>
        {a_ext(maps, e(t['maps_link']) + ARROW_UP, t, 'text-link')}
      </div>
    </div>
  </section>
</main>
""" + footer(t) + "</body>\n</html>\n"


def fill(text, code):
    vals = dict(SITE)
    vals.update(updated=UPDATED[code], tested_es=TESTED["es"], tested_en=TESTED["en"])
    if not GA:
        text = re.sub(r"<!--GA-->.*?<!--/GA-->", "", text, flags=re.S)
    else:
        text = text.replace("<!--GA-->", "").replace("<!--/GA-->", "")
    return re.sub(r"\{(\w+)\}", lambda m: e(str(vals[m.group(1)])), text)


def legal(code, page):
    t = LANGS[code]
    name = "privacy" if page == "privacy" else "accessibility"
    title_word = t["privacy"] if page == "privacy" else t["accessibility"]
    body = fill((CONTENT / "legal" / f"{name}.{code}.html").read_text(), code)
    path = PAIRS[page][code]
    desc = {"privacy": {"es": "Cómo trata Carril Diamante la información de quienes visitan su sitio.",
                        "en": "How Carril Diamante handles information about visitors to its site."},
            "accessibility": {"es": "Nuestro compromiso con la accesibilidad del sitio y cómo reportar barreras.",
                              "en": "Our commitment to an accessible site and how to report barriers."}}[page][code]
    return head(t, page, f"{title_word} · {SITE['brand']}", desc, path) + body_open("legal") + header(t, False) + f"""
<main id="main" tabindex="-1">
  <article class="container legal">
    <p class="eyebrow"><span class="eyebrow-rule" aria-hidden="true"></span>{SITE['brand']}</p>
    <h1 class="h2">{e(title_word)}</h1>
    {body}
  </article>
</main>
""" + footer(t) + "</body>\n</html>\n"


def not_found():
    t, en = LANGS["es"], LANGS["en"]
    return head(t, "home", t["notfound_title"], t["notfound_body"], "/404.html").replace(
        '<link rel="canonical"', '<meta name="robots" content="noindex"><link rel="canonical"') + body_open("404") + header(t, False) + f"""
<main id="main" tabindex="-1">
  <section class="container notfound">
    <p class="eyebrow">404</p>
    <h1 class="h2">{e(t['notfound_h1'])}</h1>
    <p class="body">{e(t['notfound_body'])} <span lang="en">{e(en['notfound_body'])}</span></p>
    <div class="actions">
      <a class="btn btn-gold" href="/">{e(t['notfound_link'])}{ARROW}</a>
      <a class="btn btn-ghost" href="/en/" lang="en">{e(en['notfound_link'])}</a>
    </div>
  </section>
</main>
""" + footer(t) + "</body>\n</html>\n"


def write(path, text):
    p = OUT / path.lstrip("/")
    if path.endswith("/"):
        p = p / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


def main():
    write("/", home("es"))
    write("/en/", home("en"))
    for page in ("privacy", "accessibility"):
        for code in ("es", "en"):
            write(PAIRS[page][code], legal(code, page))
    write("/404.html", not_found())
    today = dt.date.today().isoformat()
    urls = "".join(
        f"<url><loc>{SITE['domain']}{PAIRS[p][c]}</loc><lastmod>{today}</lastmod>"
        + "".join(f'<xhtml:link rel="alternate" hreflang="{c2}" href="{SITE["domain"]}{PAIRS[p][c2]}"/>' for c2 in ("es", "en"))
        + "</url>" for p in PAIRS for c in ("es", "en"))
    write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          f'xmlns:xhtml="http://www.w3.org/1999/xhtml">{urls}</urlset>\n')
    write("/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE['domain']}/sitemap.xml\n")
    expires = (dt.date.today() + dt.timedelta(days=365)).isoformat()
    write("/.well-known/security.txt", f"Contact: mailto:{SITE['email']}\nExpires: {expires}T00:00:00.000Z\n"
          f"Preferred-Languages: es, en\nCanonical: {SITE['domain']}/.well-known/security.txt\n")
    print("built:", ", ".join(sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*.html"))))


if __name__ == "__main__":
    main()
