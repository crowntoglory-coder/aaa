# A/B-Fahrplan Klaviyo-Flows (seine Ansage 16.09.: „thats testing 1, the winner we take and test hero image and so on and hero text“)

Mechanik: jede Mail ist in Klaviyo eine `ab-test`-Action mit 3 Varianten (A/B/C), Gewinner-Metrik unique-clicks, automatische Gewinnerwahl bei
statistischer Sicherheit; Klaviyo verschiebt die Gewichte laufend (`bin/klaviyo.py abstatus` zeigt sie). Varianten stehen im Spec (`ab: [...]`),
`flows.py build` baut `<key>~B.html`, `klaviyo.py recreate` legt den Flow neu an und startet die Tests.

| Welle | Was variiert | Felder im `ab`-Eintrag | Start |
|---|---|---|---|
| 1 | Einstieg: Betreff, Preheader, Headline/Sub (Urgency · Emoji-Urgency · Luxus · Angebot-% · Fakten · persönlich) | subject, preview, headline, sub, hero_eyebrow, big, text_open | 16.09. 04:25, 17 Tests live (+8 in Cart/Checkout 4er, Draft) |
| 2 | Hero-Bild: Spiegel-Selfie vs. Produkt-Flatlay vs. Raum/Stimmung; hell vs. dunkel | hero_image_kind (vibe1–6, room, …), hero_style (full/split/type/text) | sobald Welle 1 je Mail einen Gewinner hat (Klaviyo meldet, `abstatus`) |
| 3 | Hero-Text + Knopf: Statement vs. Nutzen vs. Frage-frei; CTA-Wortlaut („Finish checkout“ / „Back to my bag“ / „Use my 15%“) | headline, sub, cta1 | nach Welle 2 |
| 4 | Angebot/Format: Code-Leiste oben vs. unten, Countdown vs. Satz, Warenkorb-Block vs. Grid | blocks (neue Spec je Variante) | nach Welle 3 |

Regeln: Gewinner von Welle n wird Basis A von Welle n+1 (Spec anpassen, `ab` neu). Nie zwei Wellen gleichzeitig auf einer Mail. Mindestens
100 Empfänger je Variante, sonst kein Urteil (bei 0 Traffic: Welle 1 läuft, bis Ads Traffic bringen). Ergebnisse je Welle nach
`marketing/workflows/04-output/2026-MM-TT-ab-welle-N.md`.
