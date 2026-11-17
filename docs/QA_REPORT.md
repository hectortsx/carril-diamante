# Carril Diamante: QA Report

## 2026-11-13: UI/UX Pro Max review, local build

**Method:** checked the site against the skill's rule list (accessibility, touch, layout, type, motion), measured in Chrome at 390×844 touch, 844×390 touch (phone sideways) and 1440×900. The skill's generated "design system" (green/orange, Inter, Google Fonts CDN) didn't fit the brand or our no-third-party-fonts rule, so it wasn't applied.

**Fixed:**
- **Phone tap targets under 44px:** video pause button (36px), "EN" (30px wide), standalone links such as Facebook, Google Maps and the footer (22px), and the logo (38px). On touch screens they're all at least 44px now.
- **Phone sideways:** the hero buttons fell below the screen. The hero is now smaller when the screen is 500px tall or less.
- **Headings left a lone last word** ("Fotos de días de / carrera"). Added `text-wrap: balance`, plus `pretty` on paragraphs.
- **Skip link** stayed at the top of the page when Tab wrapped back to it after scrolling. It's now `position: fixed`.
- **Small text:** fact labels and the copyright line went from 13px to 14px.

**Already passing:**
- the gallery swipe hint (the next photo peeks in);
- body text 16px; line lengths are fine;
- press feedback on buttons;
- reduced motion;
- focus never hidden under the sticky header.

**Results:** release_check passes (1 owner item); browser_check: 0 problems; qa.py: 0 fails.

**New qa.py checks**, both confirmed to warn on a copy with the old CSS:
- phone targets under 44px;
- the first button below the screen on a sideways phone.

All the fixes above were also added to the starter template.

## 2026-11-13: motion improvements, local build

**Changes:**
- the fact numbers count up;
- the drone video settles from a slight zoom;
- section headings rise into place;
- on phones and touch screens the gallery is swipeable instead of auto-moving.

**Results:**
- release_check: pass (1 owner item open);
- browser_check: 0 problems;
- qa.py static and browser: 0 fails;
- heading close-ups viewed: no cut-off letters.

Checked in Chrome at 1440px, 390px with touch, and with reduced motion:
- the counters end on the real values, and screen readers get the real values;
- the video ends at normal scale;
- headings end in place;
- with reduced motion, nothing moves.

**Bug found and fixed:** the gallery pause button was always visible, even with reduced motion and on phones where it does nothing, because `.pill-btn { display: inline-flex }` overrode the `hidden` attribute. Fixed with `[hidden] { display: none !important; }`, also added to the starter template. New check in `qa.py`: "marked hidden but still visible". Confirmed it fails on a copy without the fix.

**Accessibility statement** updated (es + en) to say the gallery moves on computers and is swipeable on phones.

## 2026-11-12: pre-launch QA, local build (http://127.0.0.1:8765)

**Scope:** all 7 pages (es + en home, privacy, accessibility, 404), at 390px and 1440px, in real Chrome. Done with the `website-qa` skill.

| Check | Tool | Result |
|---|---|---|
| Static rules (lang, h1, landmarks, no inline script/style, links) | release_check.py | Pass. 1 owner item open: legal-page approval |
| Accessibility scan (WCAG 2.2 AA rules), enforced CSP, overflow, video, menu after scroll | browser_check.py | 0 problems |
| Language parity, contact links, placeholders, unused/heavy assets, AI-look heuristics | qa.py (static) | 0 fails |
| Tap targets (WCAG 2.5.8), keyboard focus on every Tab stop, layout shift, blurry/broken images, language links | qa.py (browser) | 0 fails |
| Cut-off letters in headings | close-ups of all h1/h2, viewed | None found |

**Fixed during this QA**
- Gallery photos used only the 800px files, so they were slightly soft on phones and Retina screens, and the 1600px files were shipped unused. They now use both sizes (srcset).

**Warnings accepted**
- `races.*.sub` exists only in English. Deliberate: the Spanish race names need no subtitle.

**Not done yet (manual)**
- VoiceOver pass on Mac and iPhone.
- Manual 320px reflow test.
- Hand checks: contact buttons open the right apps and numbers on a real phone; video on a real iPhone (including Low Power Mode).
- Live checks: after the first deploy, run `qa.py --live https://www.carrildiamante.com`.
