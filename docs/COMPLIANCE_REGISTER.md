# Carril Diamante: Compliance Register

This isn't legal advice. It records what was built, what was tested and when, and what the owner still needs to decide. Never describe the site as "compliant". Say what was tested and when.

## Summary (updated 2026-11-12)

**Done**
- The site has no forms, accounts, newsletter, chat or payments, so there is no personal data to collect, store or secure on our side.
- Google Analytics can only load after a visitor clicks Accept. It isn't switched on yet, because there is no measurement ID.
- Fonts, images and video come from our own domain, so no third party sees visitors before consent.
- Accessibility basics are built in: skip link, one heading per page, keyboard menu, visible focus, pause buttons for the video and the gallery, and reduced-motion support. The automated scan finds 0 problems on all 7 pages at phone and desktop width.
- The security rules for the server (content policy and headers) are written down, and tested locally with 0 violations.
- Photos are re-saved without camera or GPS data.

**Left (engineering, before or at launch)**
- Hands-on screen-reader test (VoiceOver on Mac and iPhone).
- Turn on the security headers in CloudFront and check them on the live site.
- Add a DMARC record for carrildiamante.com email when DNS moves.
- After the owner approves: fill in the accessibility statement's "what we checked" section with the test dates.

**Needs the owner**
- Approve the Privacy Policy and Accessibility Statement wording. No lawyer is recorded, so this is the owner's judgment.
- Who answers privacy requests (the policy says within 30 days) and accessibility reports (within 10 business days).
- Later: photographer credit for the 2023 photos.

**Answered 2026-11-12:** phone 720-336-9405 (Google Voice); WhatsApp 303-356-4795; email info@; legal name "Carril Diamante"; race wording and 250–300 yards confirmed; photo use permitted and people shown agree; no Google Analytics for now (the banner doesn't render); DNS moves to Route 53.

## Scoping answers (§1)
| # | Question | Answer | Date |
|---|---|---|---|
| 1 | Business name / contact / address | Carril Diamante, Hudson CO 80642. Street address not shown. Contact details unconfirmed (see above) | 2026-11-12 |
| 2 | Where are visitors | Colorado / U.S.; Spanish-speaking racing community. Unknown whether there are Mexico visitors. No data selling, no targeted ads | 2026-11-06 |
| 3 | Forms | None. Owner chose phone, WhatsApp and email links | 2026-11-06 |
| 4 | Retention / privacy requests | Policy says conversations are kept as long as needed for races, and requests get a reply within 30 days. Owner to confirm | pending |
| 5 | Analytics | None for now: owner has no GA account. The consent code ships dormant and switches on when an ID is added | 2026-11-12 |
| 6 | Features | Video (silent, self-hosted), map link (not embedded), Facebook link. No payments, accounts, newsletter, SMS, chatbot or uploads | 2026-11-12 |
| 7 | Public claims | See the claim register below | 2026-11-12 |
| 8 | Media rights | Logo: owner's. Drone video: owner's (branded). WhatsApp photos: owner says permission is given and the people shown agree; credit to be added later. The CamaraVictor10 video is **not used** (third-party branding) | 2026-11-12 |
| 9 | Lawyer | Not recorded. If none, the owner approves the legal wording | pending |
| 10 | Accessibility target | WCAG 2.2 AA | 2026-11-12 |

## Claim register
| Claim on site | Evidence | Status |
|---|---|---|
| Six-lane starting gate ("6 carriles") | Gate photo (starting-gate) shows stalls numbered 1–6 | Evidence on file |
| 250–300 yards per race | Race poster from Sat 18 March 2023 lists 300 and 250 yards; owner confirmed it's typical (2026-11-12) | Evidence on file |
| Northeast of Denver | Coordinates 40.159, −104.650 (Hudson, CO) | Evidence on file |
| Rocky Mountains on the horizon | Photos g-rockies and g-pony-up show snowy peaks behind the track | Evidence on file |
| Removed: "126 races", "Partners, lawyers…", "offices", "Jillian Smith, Founder" testimonial | Template text with no evidence | Not carried over |

## Always-on defaults (§2): evidence
- [x] `lang`, one H1, landmarks, heading order, skip link to `main[tabindex=-1]` (release_check.py, 2026-11-12, 7 pages)
- [x] No inline scripts, handlers or style attributes; JSON-LD only (release_check.py, 2026-11-12)
- [x] Fonts self-hosted: Bodoni Moda (upright + italic) and Archivo, both under the SIL Open Font License, which is shipped in assets/fonts. Montserrat replaced by Archivo on 2026-11-12
- [x] Visible focus; menu works with Enter/Space, Esc closes it and returns focus, `aria-expanded` kept in sync (site.js)
- [x] Contrast: axe found 0 color-contrast violations (browser_check.py, 2026-11-12). Text over the video sits on an 88% dark gradient
- [x] Body links underlined (legal pages, maps link)
- [x] No horizontal scroll at 390px (browser_check.py). Still to do: a manual 320px reflow test
- [x] `prefers-reduced-motion`: hero animations off, video starts paused, gallery still and scrollable
- [x] Alt text on every content image; decorative duplicates have `alt=""` and `aria-hidden`
- [x] Accessible 404 page (404.html). Still to do: return a real 404 status through CloudFront
- [x] Footer: name, contact, Privacy and Accessibility links. The Cookie settings button appears automatically once GA is on
- [ ] Manual keyboard and screen-reader pass
- Forms: not applicable (none)
- [x] Consent: nothing loads before Accept; Reject is as easy as Accept; GPC counts as a rejection; withdrawing deletes the `_ga` cookies; the `cd_consent` cookie lasts 6 months with `SameSite=Lax; Secure`; page URL is sent without query strings; Google Signals and ad personalization are off (site.js)
- [ ] In the GA admin, once the ID exists: set data retention to 2 months and turn off Signals and data sharing
- [ ] Security headers live: CSP, HSTS, nosniff, Referrer-Policy, Permissions-Policy, X-Frame-Options (source: infra/security-headers.json)
- [x] security.txt (`/.well-known/security.txt`)
- [ ] SPF ✓, DKIM ✓, **DMARC missing**: add when DNS moves (checked with dig, 2026-11-11)
- [ ] Domain auto-renew and registrar MFA (owner)

## Conditional items (§3)
- Video: silent, so no captions are needed. It has a pause button (WCAG 2.2.2) and is self-hosted, so no embed or consent is needed.
- Map: a link only, not embedded.
- Reviews and testimonials: none shown until real ones arrive with permission.
