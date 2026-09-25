# marketing — Klaviyo-Flows, Coupons, Pinterest, Popup, Meta Ads, Recherche

Alles, was Kunden außerhalb der Seite erreicht, und die Recherche dahinter. **Cashflow zuerst, Flows peak**
(seine Ansage 16.09.): die E-Mail-Flows sind das wichtigste Werkzeug der Marke — laufend testen, Gewinner
übernehmen, nie „fertig“. Werkzeug ist Klaviyo (Key in `state/klaviyo.key`), Shopify Email nur als Archiv
(`04-output/emails/`, Fassung 2). Ads nach Charley T (Andromeda One): eine CBO-Kampagne, ein Ad Set, 322-Ads,
Profit Volume statt ROAS. Pinterest: Personal-Konto @noralanelle, 30 Pins am Tag.

## Laden

- `_reference/psychologie.md` §8, `_reference/email-cro.md` §7, `_reference/funnel.md` §2, `_reference/email-design.md`
- `workflows/02-specs/2026-09-16-ab-roadmap.md` (Welle 1 Einstiegstext, Welle 2 Hero-Bild, Welle 3 Hero-Text)
- `workflows/04-output/2026-09-15-klaviyo-setup.md` (Flow-IDs, Filter, Wartezeiten, Coupons)
- `_client-context/rules.md` §Mails (Rückkauf, Chargeback, Zufriedenheit), §easy returns/kein „reply“, §Rabattcodes, §Hero trägt Urgency, §Pinterest
- Ads: `_client-context/vorbilder.md` §Charley T, `workflows/01-briefs/2026-09-10-charley-t-analyse.md`, `workflows/02-specs/2026-09-13-warmup-14-tage.md`
- `state/products-email.json` (Produkte für Mails, `flows.py snapshot`)

## Nicht laden

Bild-Fallen, Storefront-Sections, Transkripte, HANDOVER §5, die Roh-Recherche in `01-briefs/` (nur bei neuer Frage).

## Stufen-Router

| Stufe | lädt | Werkzeug | Skill / MCP |
|---|---|---|---|
| **Brief** (`workflows/01-briefs/`) | Evidenz zuerst — Reviews (sobald es welche gibt), Support-Mails, Produkttexte, Wettbewerber (Ad Library), Recherche mit Quellen; keine Performance-Daten als Evidenz | `bin/products/adlib.py`, WebSearch | Workflow (Sweep + Verifizierer) |
| **Spec** (`workflows/02-specs/`) | Mails: `state/flows-*.json` (Text, Hero, `ab`-Varianten je Mail); A/B-Fahrplan; 322-Specs (3 Creatives, 2 Texte, 2 Headlines, Hypothese „because“); Kampagnen-Spec; Primary Texts (`JJJJ-MM-TT-…-primary-text.md`) | — | Workflow (Autor-Panel + Richter für Texte) |
| **Build** (`workflows/03-builds/`, `04-output/flows/`) | `bin/flows.py build --klaviyo --no-proof` → `<key>.html`, `<key>~B.html`, `png/`; jedes HTML ansehen („not found“, Tags, Farben); Pins: `bin/pinterest.py daily` → `state/pinterest/<datum>/`; Ads: `bin/ads/builder.py`, `bin/ads/shots.py` | `bin/flows.py`, `bin/pinterest.py`, `bin/ads/` | — |
| **Output** (Klaviyo live, gepinnt, `workflows/04-output/JJJJ-MM-TT-….md`) | Mails: `bin/klaviyo.py recreate` (Templates + Flow neu, alte löschen) → `live` (Experimente starten) → `abstatus`; Codes mit Frist täglich `bin/coupons.py refresh --n 100`; Pins im Chrome (Playbook §Pinterest) → `pinterest.py done`; Bericht mit Datum | `bin/klaviyo.py`, `bin/coupons.py` | claude-in-chrome (Pinterest) |

Jede Textänderung an einer Mail = build → recreate (Klaviyo ändert Definitionen nicht per API).

## Regeln

- **Nie Rabattcode-Werte ändern ohne seine Erlaubnis** (WELCOME15 = 15 %, CHECKOUT15 = 15 %/96 h, SHIP24 = Versand/48 h).
- **„easy returns“, nie „free returns“**; kein „reply to this email“ — stattdessen Size Guide auf der Produktseite oder „buy 2 pieces if not sure“.
- Hero trägt die Urgency (verdeckt, nicht nur brandy); Absenderin „Claire, Nora Lanelle“ für Textmails; `support@nora-lanelle.com`.
- Keine Streichpreise, kein „45 % off“ in Mails (FTC 16 CFR 233.1); keine Zähler, keine erfundenen Bewertungen; Rabatt nur mit existierendem Code.
- Ziele je Mail: Wiederkaufrate hoch, Chargebacks runter, Kundenzufriedenheit hoch — jede Mail hat einen Test laufen.
- Wenn er „wie X“ sagt: X nachbauen, nicht verbessern. Gut aussehend und kurz schlägt hässlich und lang.
- Pinterest: Captions wechselnd Luxus / girly mit Emojis, Hashtags, jeder Pin verlinkt, KI-Kennzeichen an; keine Fasern, keine erfundenen Farben.
- Popup ist aus (`footer.py apply --popup` holt es zurück); Band im Footer verspricht 15 %.

## Stand (16.09.)

7 Flows / 20 Mails live, je Mail ein A/B-Test (Welle 1): checkout `UvMytE`, cart `WeibEz`, welcome `TJGveX`, browse `W67r53`,
post_purchase `UdDxfw`, post_delivery `Xmk2nZ`, winback `TBNYHB`. Coupon-Pools täglich (Plist `com.antigravity.coupons`, 04:30,
bis zur Installation aus der Sitzung). Pinterest: 30 Pins am 16.09., Vorrat 19 Tage. Warm-up-Primary-Text: `02-specs/2026-09-16-warmup-primary-text.md`.
Wartet auf ihn: `! bin/go.sh` (Onsite-Tracking), Klaviyo Sending Domain, Ad-Account + Pixel.
