# Carril Diamante: Website Intake

> **Owner answers, 2026-11-12:**
> - ✅ Phone **720-336-9405**, a Google Voice number used for calls and texts (the Facebook banner's 9505 was wrong).
> - ✅ WhatsApp **303-356-4795**, a separate number. It's used only in the WhatsApp button and isn't shown as text.
> - ✅ Email **info@carrildiamante.com**
> - ✅ Legal name **Carril Diamante**
> - ✅ Race descriptions (Parejeras / Abiertas, as drafted from the March 2023 poster) are correct
> - ✅ "250–300 yards" is typical
> - ✅ Photo rights: the 2023 WhatsApp photos may be used, and the people shown agree. Photographer credit to be added later.
> - ✅ No Google Analytics yet. The code stays dormant; add the ID later if they want it.
> - ✅ DNS: moving to AWS Route 53
> - ⚠ Still open: approval of the Privacy and Accessibility pages, and who answers privacy and accessibility requests.
> - The "El Regalo vs El 5to Mes" video belongs to CamaraVictor10 and is **not used**.

Fill in every `[ ]` line. Leave a line blank if you don't know, but don't guess. Started 2026-11-11.

## 1. Business
- Business name shown on the site: **Carril Diamante**
- [ ] Legal business name (LLC, etc.):
- [ ] One-sentence description, in your own words:
- [ ] Location to show publicly. Choose one: `Hudson, CO` only / full street address:
- [ ] Street address (even if not shown):
- [ ] Phone number:
- [ ] WhatsApp number (same as phone?):
- [ ] Email: `info@carrildiamante.com`? Is this inbox monitored?
- [ ] Hours or race days and season:

## 2. Races and services
- [ ] **Carreras Abiertas**: what it is, who can enter, entry fee:
- [ ] **Carreras Parejeras**: what it is, who can enter, entry fee:
- [ ] **Cuadrilla**: what it means at your track:
- [ ] Other things visitors come for (spectating, events, food, horse boarding, training):
- [ ] What should a racer do to register? (call / WhatsApp / email; what information should they send?)
- [ ] What should a spectator know? (tickets, parking, kids, rules):

## 3. Claims. Only include what you can back up.
- [ ] "126 races": true? Over what period?
- [ ] "6 cuadrillas": true?
- [ ] "6 carriles" (lanes): true?
- [ ] Years in operation:
- [ ] Any licenses, sanctioning bodies, insurance, awards to mention:
- [ ] Real testimonials (name and permission to publish). The current "Jillian Smith" quote will be removed unless it's real:

## 4. Media. Put files in `Carril_Diamante/assets/`
- [ ] Logo: SVG preferred, or the largest PNG with a transparent background
- [ ] Videos: races, track, horses (any format; I'll compress them)
- [ ] Photos
- [ ] For each file: do you own it, or have permission to use it?
- [ ] Do people who can be recognized in the videos or photos agree to appear on the site?

## 5. Online presence
- [ ] Facebook: https://www.facebook.com/carrildiamante (correct?)
- [ ] Instagram:
- [ ] TikTok:
- [ ] YouTube:
- [ ] Google Business Profile link (if any):

## 6. Language
- Decided: **bilingual English / Spanish with a toggle**
- [ ] Which language should load first? Spanish or English:
- [ ] Who checks the Spanish copy before launch?

## 7. Privacy, analytics, legal
- Decided: **Google Analytics, loaded only after the visitor clicks Accept**
- [ ] Google Analytics Measurement ID (`G-…`), or "create one for me":
- [ ] Do you have a lawyer? If not, you approve the privacy policy wording yourself (this gets recorded).
- [ ] Do visitors come from outside the U.S. (e.g. Mexico)?
- [ ] Who handles privacy requests (name and email), and within how many days?
- [ ] Is anyone under 13 expected to use the site?

## 8. Domain and hosting
- Domain: `carrildiamante.com`, registered at Google Domains / Squarespace; site currently on Duda.
- [ ] Who has the login for the domain registrar?
- [ ] DNS. Choose one: **move to AWS Route 53** (recommended, ~$0.50/mo) / keep at Squarespace and change records there
- Email on this domain: **Google Workspace** (checked 2026-11-11: MX = aspmx.l.google.com; SPF and DKIM present; **no DMARC record**, so add `_dmarc` when DNS moves). All MX, SPF and DKIM records must be copied to the new DNS exactly before switching.
- [ ] When does the Duda plan renew? (cancel only after the new site is live)

## 9. Look and feel
- Proposed: "night race". Black/charcoal, diamond-gold accent, dust-tan neutral; full-screen race video hero.
- [ ] OK, or other preferences or sites you like:
- [ ] Colors from the logo that must be used:
