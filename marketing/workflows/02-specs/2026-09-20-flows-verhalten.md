# Spec: Flows nach VERHALTEN — „jeder customer soll je nach behavior die richtige sequenz bekommen“ (20.09.2026, ~14:35)

Seine Ansage 20.09. ~14:20 (rules.md §Seine Antworten 20.09. (~14:20), wörtlich): „was heißt aber welle ? jeder customer soll jenach behavior die richtige
sequenz bekommen, einen perfekten ablauf um zu verkaufen.“ … „baue alle emails genau so und mache als entwurf in klaviyo wenn ich go sage kannst du live
schalten, will wirklich lange sequenzen sehen die synergieren und effizient sind, keine einzige email darf gewastet sein das ist sehr wichtig. und der kunde
darf net zu gespamt werden researche wie es 8 fig fashion stores machen die auf high aov gehen.“ — zweite Erwähnung (17.09. „Flows bis 30 Mails“).
Rolle: Research + Spec (urteil). Nichts gebaut, kein Klaviyo-Schreibzugriff, kein Telegram. Ersetzt die Wellen-Logik aus `02-specs/2026-09-20-flows-30-tage.md`
(§7) — die 45 Mails aus dieser Spec bleiben, sie werden nur anders verteilt: nach Zustand, nicht nach Bau-Datum.
Gelesen: 30-tage-Spec · `bin/klaviyo.py` (Docstring, PLAN, `steps()`, `filters()`, `flow()`, `recreate()`, `abreport()`) · `state/klaviyo/plan.json` · `marketing/CONTEXT.md` ·
funnel.md §2 · email-cro.md §2/§7 · psychologie.md §8 · rules.md §Cashflow/§Hero/§Rabattcode/§Antworten 20.09. (beide) · `01-briefs/2026-09-13-klaviyo/api-research.md`.

## 0. Antwort in drei Zeilen

1. **Verhalten statt Wellen: 8 Zustände, 10 Verzweigungen, 45 Mails — keine Kundin sieht mehr als 3 Flow-Mails/Woche, Service-Mails ausgenommen.**
   8-stellige Fashion-Brands mit hohem AOV senden *weniger*, nicht mehr: Jenni Kayne −43,8 % Sendungen, +14,5 % Mail-Umsatz; DKNY −24 % Sendungen, +8 % Klicks,
   30 % des Klaviyo-Werts aus Flows (Quellen 10/11). Die Dichte entsteht aus Verzweigung (Erstkäuferin ≠ Wiederkäuferin ≠ heißer Checkout ≥ $150), nicht aus Menge.
2. **Was `bin/klaviyo.py` heute kann:** Trigger (Liste/Metrik) → Delay → Mail-Ketten, Flow-Filter (`profile_filter`, gilt an jedem Schritt, wirft raus), `delay_until_time`,
   Smart Sending je Mail, A/B-Action. **Kann es nicht:** `conditional-split`, `trigger-split`, Filter je einzelner Mail (`additional_filters`), Segment-Trigger — im Code geprüft
   (`grep -n split bin/klaviyo.py` → nur ein TODO-Kommentar Zeile 57). Zwei Erweiterungen reichen für 8 der 10 Verzweigungen: `conditional-split`-Action (Schema aus der
   OpenAPI, §5) und `additional_filters` je Mail (Feld existiert schon im Message-Objekt, steht auf `null`).
3. **Heute als Entwurf:** welcome (2 Splits), post_delivery (2 Splits, VIP-Pfad statt eigenem VIP-Flow), winback (2 Splits) per Skript; cart/checkout ≥ $150 (Trigger-Split)
   und sunset (Segment-Trigger) im UI nachbauen. Live erst auf sein „go“ — dafür braucht `recreate` einen `--draft`-Schalter (heute setzt es live, wenn der alte Flow live war).

## 1. Research — wie 8-stellige Fashion-DTC-Brands mit AOV ≥ $150 verzweigen (jede Zahl mit URL + Datum)

| # | Quelle (Datum) | Verzweigungs-Regel / Zahl |
|---|---|---|
| 1 | Klaviyo Help „Multi-Branch Splits“ (30.06.2026) https://help.klaviyo.com/hc/en-us/articles/52369094030235 | Bedingungen: Metrik/Event, Profil-Eigenschaft, Ort, Listen-/Segment-Zugehörigkeit, Consent, Predictive (CLV, Churn), Random Sample, **Trigger-Event-Daten (nur Metrik-Flows)**; Pfade „in the order you define them, routed down the first one they qualify for“; max. 20 Pfade (19 + „Everyone else“) |
| 2 | Klaviyo Help „Branching best practices“ (07.07.2025) https://help.klaviyo.com/hc/en-us/articles/360051182592 | Muster 1: „Has Placed Order at least once over all time“ → Käuferin-Pfad, Rest „Everyone else“; Code nur Erstkäuferinnen („Take 10% off your first purchase“). Muster 2: Kategorie-Split nur in Metrik-Flows, **spezifischste Kategorie zuerst**, immer ein „Everyone else“ |
| 3 | Klaviyo Help „Understanding flow branching“ (18.11.2025) https://help.klaviyo.com/hc/en-us/articles/115003883992 | Bedingung wird geprüft, **wenn das Profil den Split erreicht**; Falle: „there isn't sufficient time between the action processing“ → Delay vor jedem Engagement-Split |
| 4 | Klaviyo Help „Optimize flow sending frequency“ https://help.klaviyo.com/hc/en-us/articles/10948996125083 | Empfohlene Delays: Welcome sofort · 1 d · 1 Woche; Cart sofort · 2 h · 1 d; Browse 2 h · 4 h · 1 Woche; Post-Purchase 1 · 3 · 4 d; Winback 2 Wochen · 3 Monate; Sunset 2 Monate. Smart Sending „will not enable … by default“ je Flow-Mail; Frequenz-Test = Split „Random sample“ |
| 5 | Kinetic „Advanced Klaviyo Flows“ (03.06.2026) https://www.usekinetic.com/blog/klaviyo-flows-advanced | **Warenkorb-Wert-Split: < $50 kein Rabatt · $50–200 Rabatt erst Mail 3 · > $200 „higher-touch“ mit Service-Note**; Kundinnen-Typ: 1. Kauf = Story + Produkt-Education · 2. Kauf = Intro überspringen, VIP andeuten · 3+ = Status + Neues; Cross-Sell Durables 1–2 Wochen nach Zustellung; Tests 2–4 Wochen, Welcome/Cart 6–8 Tests/Jahr |
| 6 | Attribuly „Post-Purchase Repeat-Customer Blueprints“ (23.05.2026) https://attribuly.com/blogs/klaviyo-post-purchase-flow-repeat-customer-blueprints/ | „Trigger on Placed Order. Add a conditional split for first time customers“; wer während des Flows erneut kauft → unterdrücken; Erstkäuferin 4 Mails (0 · nach Versand · 3–7 d nach Zustellung Review · 7–21 d Cross-Sell „if no second order“); Cross-Sell bei hoher Überlegung erst Tag 21 |
| 7 | Mailflow Authority „Klaviyo Flows: Deliverability“ (04/2026) https://mailflowauthority.com/email-automation/klaviyo-flows-deliverability | **Frequency Cap als Filter: „Has received email at most 3 times in the last 7 days“**; Browse „been in this flow zero times in the last 30 days“; Cart „not been in this flow in the last 7 days“; Smart Sending überspringt, verschiebt nicht; Engagement-Split „opened or clicked at least once in the last 90 days“; Winback-Eintritt „emailed ≥ 5 times ∧ not opened 90 days“; Suppression ab 120 d inaktiv; Open < 15 % = zu viele Inaktive; Spam < 0,1 % |
| 8 | Digital Applied „Lifecycle Flows 2026 Playbook“ (29.06.2026) https://www.digitalapplied.com/blog/klaviyo-lifecycle-email-flows-ecommerce-2026-playbook | Checkout: „Tune incentive and timing by AOV bucket rather than blanket discounting“; **Cart-RPR nach AOV: $100–200 = $7,01 · $200+ = $14,14**; Benchmarks (BS&Co, 14 Marken): Welcome CR 4,37 % RPR $2,51 · Checkout 2,30 % $3,55 · Cart 1,82 % $3,56 · Browse 0,61 % $0,92 · Post-Purchase 0,31 % $0,47 (Open 58 % = höchste, Umsatz niedrigste) · Winback 0,09 % $0,07; VIP über Predictive CLV/RFM, nicht Schwellenwert; Sunset: kein Open/Klick 12 Monate, Outlook 6 Monate |
| 9 | Eightx „Flow revenue benchmarks by brand stage“ (27.06.2026) https://eightx.co/blog/average-klaviyo-flow-revenue-contribution-benchmarks | Flow-Anteil am Mail-Umsatz: < $5 Mio 25–35 % · $5–20 Mio 40–50 % · > $20 Mio 50–60 % · P90 58–65 %; RPR Ø/P90: Cart $3,65/$28,89 · Welcome $2,65/$21,18 · Browse $1,07/$7,21 · Winback $0,84 · Back-in-stock $9,14 (conv 6,72 %) · Kampagne $0,11; **Prüne-Flags: Cart < $2/Empfängerin, Welcome < $1,50** |
| 10 | Klaviyo Case Study Jenni Kayne (Luxus-Fashion, Q1 2023) https://www.klaviyo.com/customers/case-studies/jenni-kayne-email-efficiency | **−43,8 % Sendungen, +14,5 % Mail-Umsatz, +22 % Gesamtumsatz, +35 % Kampagnen-Klicks**; max. 1 Kampagne/Tag; Interessen-Split Apparel vs. Home; Warenkorb > $5.000 → Store-Manager ruft an; „It doesn't feel like a luxury experience to be getting 3 emails a day“ |
| 11 | Klaviyo Case Study DKNY (Stand 06/2026) https://www.klaviyo.com/customers/case-studies/dkny | 1,2 Mio Abonnentinnen; **30 % des Klaviyo-Werts aus Flows; −24 % Sendungen, +8 % Klickrate**; Split nach AOV-Historie (Deal-Hunter bekommen die Rabatt-Mails, andere nicht); Welcome nach Kanal (Store vs. Online); Price-Drop-Flow; „when we have a sale 3 months from now, that message stands out“ |
| 12 | Klaviyo Blog „Fashion best practices“ (18.09.2024) https://www.klaviyo.com/blog/fashion-ecommerce-marketing-best-practices | 51 % kaufen Mode „a few times a year“, 36 % monatlich (= Wiederkauf-Fenster 60–120 d); Little Sleepies Engagement-Segmente +138,2 % Mail-Umsatz; Cargo Crew Post-Purchase A/B 3,5× RPR; Marine Layer Welcome nach Quelle +40,4 % |
| 13 | Klaviyo Community „Multi-Email Flows for High-Value Products“ https://community.klaviyo.com/marketing-30/best-practices-for-multi-email-flows-for-high-value-ecommerce-products-18738 | Post-Purchase 3 · 7 · 14 d; 70–80 % Education/Reassurance, 20–30 % Angebot; Flow-Priorität per Split „already in High-Value flow?“ oder Filter „received email (flow) equals zero times“ |
| 14 | Nudgify „Conditional vs Trigger Split“ (14.03.2025) https://www.nudgify.com/conditional-split-vs-trigger-split-klaviyo/ | Trigger-Split prüft Event-Eigenschaften (`$value`, Kategorie) — für Warenkorb-Wert; Conditional-Split prüft Profil + Vergangenheit (geöffnet, geklickt); „Allow sufficient time for profile updates before conditional evaluation points“ |
| 15 | Klaviyo OpenAPI `create_flow.json` (Fetch 13.09., `01-briefs/2026-09-13-klaviyo/api-research.md` Z. 50–96) https://developers.klaviyo.com/en/reference/create_flow · https://github.com/klaviyo/openapi | Action-Enum enthält `conditional-split`, `trigger-split`, `ab-test`, `update-profile-property`, `list-update`; `conditional-split` = `data.profile_filter.condition_groups` + `links.next_if_true/next_if_false`; Condition `profile-metric` mit `measurement count|sum`, Operatoren `equals … not-equals`, `timeframe_filter` `flow-start | in-the-last | alltime`; `FlowEmail.additional_filters` (nullable) je Mail. Create Flow 100/Tag. (developers.klaviyo.com liefert heute 403 für den Fetch — Zahlen aus dem Brief vom 13.09.) |

**Drei Sätze aus dem Research, die die Spec tragen:** (a) Verzweigt wird an 3 Achsen — Kaufhistorie (0 / 1 / 2+), Wert des Auslösers (≥ $150) und Engagement im Flow (geklickt seit Start) —
alles andere (Palette, Größe, Kategorie) braucht Profil-Eigenschaften, die wir noch nicht sammeln (Popup ohne Präferenz-Feld, Onsite-Tracking wartet auf `bin/go.sh`). (b) Die Kappe ist ein Filter,
kein Gefühl: „received email ≤ 3 in 7 days“ je Content-Mail, Service-Mails frei. (c) Verschwendet ist eine Mail, die pro Empfängerin unter dem Flow-Floor liegt (Quelle 9: Cart < $2, Welcome < $1,50
je Flow → je Mail geteilt durch Mailzahl) oder die Unsubscribe > 0,2 % kostet — nicht eine Mail, die „nur“ nicht geöffnet wird (Post-Purchase: Open 58 %, RPR $0,47).

## 2. Prinzip „jede Kundin, ihre Sequenz“ — Zustände und Übergänge

Zustand = das, was Klaviyo über die Frau messen kann, heute, ohne neue Datenfelder. Jede Frau ist in genau einem Kauf-Zustand und höchstens einem Absicht-Zustand.

| Zustand | Klaviyo-Signal | Flow, der sie trägt | verlässt den Zustand durch |
|---|---|---|---|
| **Anmelderin** | in Liste, Placed Order = 0 (alltime) | welcome (8, Pfad „neu“) | Kauf → Käuferin 1; Viewed Product → + Browserin; 21 d ohne Klick → inaktiv-Kandidatin |
| **Browserin** | Viewed Product (braucht Onsite-JS, `bin/go.sh` = sein Klick) | browse (3) | Added to Cart → Warenkorb; Kauf; 72 h Ende |
| **Warenkorb** | Added to Cart, Checkout Started = 0 | cart (4; ≥ $150 = Pfad „heiß“) | Checkout Started → Checkout; Kauf; 73 h Ende |
| **Checkout** | Checkout Started, Placed Order = 0 seit Start | checkout (4; ≥ $150 = Pfad „heiß“, 2 Codes) | Kauf; 73 h Ende |
| **Käuferin 1** | Placed Order = 1 (alltime) | post_purchase (3, Service) → post_delivery Pfad „erst“ (12) | 2. Kauf → Käuferin 2+; Storno/Erstattung → Kette stoppt; Tag 90 ohne Kauf → winback „erst“ |
| **Käuferin 2+** | Placed Order ≥ 2 | post_purchase (3) → post_delivery Pfad „wieder“ (7 = 4 Service + 3 VIP) | Tag 90 → winback „wieder“ |
| **VIP** | = Käuferin 2+ ab Mail vip-1 (kein eigener Flow; Predictive CLV erst ab 500 Kundinnen, Quelle 8) | Pfad „wieder“ in post_delivery, Kampagnen-Segment „VIP“ | — |
| **inaktiv** | kein Open/Klick 90 d ∧ ≥ 5 Mails erhalten ∧ Placed Order = 0 in 90 d (Quelle 7) | sunset (2, Segment-Trigger, UI) | Klick → zurück (Segment-Austritt); 14 d ohne Klick → Suppression |

Übergänge, die Mails STOPPEN (Flow-Filter, gilt an jedem Schritt, im PLAN heute ✅): Kauf stoppt welcome/browse/cart/checkout (`Placed Order = 0 since flow-start`); Checkout stoppt cart
(`Checkout Started = 0`); Warenkorb/Checkout stoppt browse; Versand stoppt post_purchase; neuer Kauf, Storno, Erstattung stoppen post_delivery und starten es neu (`reentry alltime/0`).
Übergänge, die Mails ÜBERSPRINGEN (Filter je Mail, `additional_filters`, NEU): Frequenz-Kappe (§4), „nur wenn geklickt“ (§3), „nicht während Checkout-Flow“ (welcome/browse-Content).

## 3. Verzweigungsbaum je Flow (Text-Diagramm) — Bedingung → Pfad → Mails (Key · Tag · Zweck · Code-Regel)

Legende: `[S]` = conditional-split (API, §5) · `[T]` = trigger-split (UI, Event-Wert) · `[F]` = Filter je Mail (`additional_filters`) · `⏹` = Abbruch durch Flow-Filter · ★ = Smart Sending aus.
Codes: WELCOME15 (Erstkundin, stehend, keine Frist) · NL15-Pool (15 %, 96 h, nur bestehender Wert) · SHIP-Pool (Versand, 48 h). **Nie neue Werte, nie Descriptor** (rules 20.09. Antwort 5/6).

### welcome (Trigger Liste; ⏹ Placed Order seit Start; Wiedereintritt nie)

```
welcome (Tag 0, WELCOME15, ★)
└─[S1 sofort danach] Placed Order ≥ 1 alltime?            ← Kundin, die sich neu anmeldet (Popup/Footer) — Quelle 2
   ├─ JA  „Kundin“ (2 Mails): welcome-1b Tag 1 (Claire, Text; Fuß-Satz ohne Code) → welcome-7 Tag 8 („stay or go“: Coats & knits / Everything)
   │        [F] welcome: bekommt sie trotzdem (Klaviyo sendet Mail 1 vor dem Split); Betreff-Variante ohne „first order“ = A/B-Variante C (heute schon ab)
   └─ NEIN „neu“: welcome-1b Tag 1 (Claire) → welcome-2 Tag 3 (Social Proof) → welcome-6 Tag 5 (drei Looks, WELCOME15)
        └─[S2 Tag 7, 07:00] Clicked Email ≥ 1 seit Flow-Start?  ← Klick, nicht Open (MPP; email-cro §7.10)
           ├─ JA  „warm“ (4): welcome-3 Tag 7 (Bestseller) → welcome-4 Tag 10 (Passform/easy returns) → welcome-5 Tag 14 (Einwände: Versand, Größe) → welcome-7 Tag 21 („stay or go“)
           └─ NEIN „kalt“ (2): welcome-4 Tag 10 (Passform/easy returns = der Einwand, der Nicht-Klickerinnen hält) → welcome-7 Tag 14 („stay or go“; kein Klick → Sunset-Kandidatin)
                 gespart: welcome-3, welcome-5 (2 Mails × ~60 % Nicht-Klickerinnen = ~1,2 Mails/Anmelderin ohne Umsatz)
[F] alle Content-Mails (1b, 2, 6, 3, 4, 5, 7): Received Email ≤ 2 in 7 d ∧ Checkout Started = 0 in 3 d   (Kappe; Checkout-Flow hat Vorrang)
```
Zweck-Kette: Code (Tag 0) → Marke (1) → Beweis (3) → Wahl (5) → Bestseller (7) → Risiko umgedreht (10) → Einwände (14) → Entscheidung (21). Kein „Code endet“ (WELCOME15 hat keine Frist).

### browse (Trigger Viewed Product; ⏹ Placed Order, Added to Cart, Checkout Started seit Start; Wiedereintritt 7 d)

```
[S3 am Eintritt] Placed Order ≥ 1 alltime?                ← ersetzt den harten LAST14-Filter (heute fliegt die Käuferin raus)
├─ JA  „Kundin“ (1): browse Tag 0+1 h — Variante ohne WELCOME15 (A/B-Variante „Kundin“: „your size, in this one“), Ende
└─ NEIN „neu“ (3): browse +1 h (Detail, das die Seite nicht zeigte; kein Rabatt) → browse-2 +25 h (Stimme zum Teil, WELCOME15 im Fuß)
     └─ browse-3 +73 h  [F] Clicked Email ≥ 1 seit Start   ← Nicht-Klickerin bekommt Mail 3 nicht (Browse-RPR $0,92 auf 3 Mails = $0,31/Mail; für Nicht-Klickerinnen ≈ 0)
[F] alle: Received Email ≤ 2 in 7 d
```
Bis `bin/go.sh` (Onsite-Tracking) läuft, feuert dieser Flow nicht — Spec gilt ab seinem Klick.

### cart (Trigger Added to Cart; ⏹ Placed Order, Checkout Started; Wiedereintritt 7 d)

```
[T1 am Eintritt, UI] Event $value ≥ 150?                  ← Quellen 5/8: > $200 „higher-touch“, Cart-RPR $14,14 bei AOV 200+; seine Antwort 5: heiße Checkouts 2 Codes
├─ JA  „heiß“ (4): ca4-1 +1 h ★ (nur das Teil, easy returns, Liefertermin) → ca4-2 +25 h (Claire, NL15-Pool **+ SHIP-Pool** = 2 Codes) → ca4-3 +49 h (Code groß, 48 h) → ca4-4 +73 h (letzte: Versand-Pool)
└─ NEIN „normal“ (4): ca4-1 +1 h ★ → ca4-2 +25 h (Claire + NL15-Pool) → ca4-3 +49 h → ca4-4 +73 h (SHIP)
[F] ca4-3, ca4-4: Clicked Email ≥ 1 seit Start ∨ Viewed Product ≥ 1 in 2 d   ← Nicht-Klickerin ohne Rückkehr auf die Seite: Mail 3/4 gespart (Rabatt-Exposition ohne Absicht)
[F] ca4-2..4: Received Email ≤ 3 in 7 d   (Cart darf 1 mehr als Content — höchster RPR aller Flows)
```
Kein Käuferin-Split hier: Wiederkäuferin mit Warenkorb = echte Zweitkauf-Absicht, Code passt (30-tage-Spec §5.2).

### checkout (Trigger Checkout Started; ⏹ Placed Order; Wiedereintritt 7 d)

```
[T2 am Eintritt, UI] Event $value ≥ 150?
├─ JA  „heiß“: co4-1 +75 min ★ (Produkt, Preis, was sie stoppte; ein Knopf) → co4-2 +25 h (NL15-Pool + SHIP-Pool, „express if over $150“ nur wenn Express-Rate im Shop existiert — sonst Versand-Pool) → co4-3 +49 h → co4-4 +73 h
└─ NEIN „normal“: co4-1 ★ → co4-2 (NL15-Pool) → co4-3 → co4-4 (SHIP)
[F] co4-3, co4-4: Clicked Email ≥ 1 seit Start ∨ Checkout Started ≥ 2 seit Start   ← sie war wieder im Checkout = weiter; sonst Mail 3/4 gespart
[F] co4-2..4: Received Email ≤ 3 in 7 d
```

### post_purchase (Trigger Placed Order; ⏹ Fulfilled Order; Wiedereintritt jede Bestellung) — Service, keine Verzweigung, keine Kappe

post_purchase Tag 0 ★ (Dank, was passiert; verkauft nichts; **Descriptor-Zeile raus**) → post_purchase-next +24 h ★ (Größe/Adresse prüfen, easy returns) → post_purchase-wait Tag 5 ★ (noch nicht verschickt: ehrlich, Kontakt support@).
Ziel je Mail: Support-Tickets „wo ist mein Paket“ und Chargebacks, nicht RPR (rules §Mails 15.09.).

### post_delivery (Trigger Fulfilled Order; ⏹ Placed Order, Cancelled Order, Refunded Order seit Start; Wiedereintritt jede Bestellung)

```
post_purchase-transit Tag 3 ★ → post_delivery-arriving Tag 7 ★ → post_delivery-arrived Tag 11 ★     ← Service für alle
└─[S4 Tag 11, nach arrived] Placed Order ≥ 2 alltime?      ← Quellen 5/6: 2. Kauf = Intro überspringen; kein Rabatt an Wiederkäuferin (Marge)
   ├─ JA  „wieder“ (4 weitere = VIP-Pfad, ersetzt den VIP-Flow der 30-tage-Spec): post_purchase-3 Tag 18 (Passform-Bitte, kurz) →
   │        vip-1 Tag 20 (Claire, Text: „second order. You know the fit; here's my direct line“) → vip-2 Tag 28 („first look“ 4 neueste Teile, 48 h vor Kampagne) →
   │        vip-3 Tag 45 („your palette, complete“, SHIP-Pool = VIP-Anreiz, entschieden 20.09.) → post_delivery-newin Tag 60
   │        gespart gegenüber „erst“: wear, crosssell+Code, code2, ugc, style, season (6 Mails, davon 2 mit Rabatt-Exposition)
   └─ NEIN „erst“ (9 weitere): post_purchase-2 Tag 14 (so trägst du es) → post_purchase-3 Tag 18 (Passform) → post_delivery-crosssell Tag 24 (2. Teil zur Palette, NL15-Pool) →
        post_delivery-code2 Tag 27 [F] Clicked Email ≥ 1 in 7 d (Code-Ende nur, wer den Cross-Sell geklickt hat — sonst Rabatt-Erinnerung an Desinteresse = verschwendet)
        └─[S5 Tag 33, 07:00] Clicked Email ≥ 1 seit Flow-Start?
           ├─ JA  „warm“: post_delivery-ugc Tag 33 (Foto-Bitte) → post_delivery-style Tag 38 (3 Arten zu tragen) → post_delivery-vip Tag 45 (Vorab-Zugang) → post_delivery-season Tag 52 → post_delivery-newin Tag 60
           └─ NEIN „kalt“: post_delivery-vip Tag 45 → post_delivery-newin Tag 60      ← 3 Content-Mails gespart; Tag 90 winback entscheidet
[F] alle Nicht-Service-Mails (ab Tag 14): Received Email ≤ 2 in 7 d
```

### winback (Trigger Placed Order, erste Mail Tag 90; ⏹ Placed Order seit Start; Wiedereintritt jede Bestellung)

```
[S6 Tag 90 am Eintritt] Placed Order ≥ 2 alltime?
├─ JA  „wieder“ (3): winback Tag 90 (Neues, kurz, 3–6 Teile — nie „we miss you“) → winback-2 Tag 97 (Saison) → winback-5 Tag 118 („new season, same size“, SHIP-Pool)   ← kein Rabatt
└─ NEIN „erst“ (4): winback Tag 90 → winback-2 Tag 97 → winback-3 Tag 104 (NL15-Pool, 96 h) → winback-4 Tag 118 (letzte Chance, Code läuft)
     └─[S7 Tag 150] Clicked Email ≥ 1 seit Flow-Start?
        ├─ JA: winback-5 Tag 150 (New-In, letzte Mail, dann Ruhe)
        └─ NEIN: keine Mail → Segment „inaktiv“ übernimmt (sunset)
[F] alle: Received Email ≤ 2 in 7 d
```

### sunset (Trigger Segment „inaktiv“: Opened/Clicked Email = 0 in 90 d ∧ Received Email ≥ 5 alltime ∧ Placed Order = 0 in 90 d ∧ Profil > 30 d — UI, Segment-Trigger fehlt im Skript)

```
sunset Tag 0 („still want these?“ — ein Knopf „stay“)
└─[S8 Tag 14] Clicked Email ≥ 1 seit Flow-Start?
   ├─ JA: Ende (Segment-Austritt durch den Klick)
   └─ NEIN: sunset-2 („last one from us“, Knopf „stay“) → Tag 21 [S9] Clicked? NEIN → Action `update-profile-property` suppress=true → Kampagnen-Ausschluss (Quelle 7/8)
```

**Zählung:** 45 Mails (wie 30-tage-Spec: welcome 8 · browse 3 · cart 4 · checkout 4 · post_purchase 3 · post_delivery 12 + vip 3 · winback 5 · sunset 2 · backinstock 1) — VIP-Mails wandern in den
„wieder“-Pfad von post_delivery (kein eigener Flow, keine Kollision mit Tag 7/27/33). **Verzweigungen NEU: 9 Splits (S1–S9) + 2 Trigger-Splits (T1, T2) = 11; Filter je Mail NEU: 4 Absichts-Filter
(browse-3, ca4-3/4, co4-3/4, code2) + Kappe auf 31 Content-Mails.** Längste Sequenz einer Erstkäuferin, die klickt: 3 + 12 = 15 Mails Tag 0–62 (1,7/Woche); kürzeste einer kalten Wiederkäuferin: 3 + 7 = 10.

## 4. Frequenz-Kappe und Priorität bei Kollision

**Kappe (Quelle 7, als Filter je Mail, nicht als Flow-Filter — ein Flow-Filter wirft die Frau aus der Kette, ein Mail-Filter überspringt nur diese Mail):**
- Content-Mails: `Received Email` count ≤ 2 in the last 7 days → die Mail ist höchstens die 3. der Woche. Cart/Checkout ≤ 3 (höchster RPR, kurze Kette).
- Ausgenommen (kein Filter, ★ kein Smart Sending): post_purchase ×3, transit, arriving, arrived, ca4-1, co4-1, welcome Tag 0 = 9 Mails. Kampagnen zählen in „Received Email“ mit → 2 Kampagnen in der Woche drosseln die Flow-Content-Mails automatisch auf 1.
- Ergebnis: max. 3 Flow-Mails/Woche je Profil + Service; mit 1–2 Kampagnen ≤ 5/Woche (Return-Path-Schwelle, email-cro §2; Jenni Kayne: 1 Kampagne/Tag als Deckel — wir bleiben darunter).

**Priorität bei Kollision am selben Tag** — Klaviyo hat keine Rangliste; die Reihenfolge entsteht aus drei Hebeln (Smart Sending 16 h überspringt die zweite, verschiebt nicht; Flow-Filter; Mail-Filter):
`Post-Purchase/Service (★) > Checkout (co4-1 ★, Flow-Filter wirft cart raus) > Cart (ca4-1 ★, Flow-Filter wirft browse raus) > Browse (Smart Sending) > Welcome (Smart Sending + [F] Checkout Started = 0 in 3 d) > Kampagne (Smart Sending an)`.
Post-Delivery-Content vs. Welcome kollidiert nie (Käuferin verlässt welcome durch ⏹). Browse vs. Welcome: beide Smart Sending, die frühere gewinnt (browse +1 h nach View, welcome 07:00) — hinnehmbar, browse ist die aktuellere Absicht.
Zwei Flow-Mails am selben Tag: alle Tages-Delays `07:00` Ortszeit + Smart Sending (30-tage-Spec §5.5 ✅).

## 5. „Keine Mail verschwendet“ — Ziel je Mail, Abschaltregel, `abreport`

Verschwendet = kein Umsatzbeitrag UND kein Service-Zweck. Messung je Mail über `bin/klaviyo.py abreport` (liefert heute schon Empfänger/Klicks/Umsatz je `flow_message_id`, Zeile 325–341) —
Erweiterung: je Mail RPR = Umsatz/Empfängerinnen, Klick-zu-Öffnung, Unsubscribe; Ampel nach Tabelle; Ausgabe `state/klaviyo/waste.json` + Telegram-Zeile je roter Mail. Prüfung wöchentlich (Plist `weekly`), Urteil erst ab **500 Empfängerinnen je Mail** (Quelle 5: 2–4 Wochen je Test; kleine Zahlen lügen).

| Flow | Floor je Flow (Quellen 8/9) | **RPR-Schwelle je Mail (raus, wenn darunter nach 500 Empf.)** | Klick-Ziel je Mail | Zusatz-Abschalter |
|---|---|---|---|---|
| welcome | RPR $2,51–2,65 Ø, Prüne < $1,50 | Mail 1: $0,80 · Mails 2–8: $0,20 | Mail 1 ≥ 6 %, sonst ≥ 2 % | Unsub > 0,2 % je Mail |
| browse | $0,92–1,07 | $0,20 | ≥ 2 % | Mail 3 raus, wenn RPR < 50 % von Mail 2 |
| cart | $3,56–3,65, Prüne < $2 | $0,60 (AOV ≥ $150: Ziel $1,50; Quelle 8: $7,01 je Flow bei AOV 100–200) | ≥ 4 % | Code-Mail (ca4-3): Bestellungen mit Code < 30 % aller Cart-Bestellungen → Code eine Mail später |
| checkout | $3,55 | $0,80 | ≥ 5 % | wie cart |
| post_purchase (Service) | RPR nicht das Ziel (Open 58 %, RPR $0,47) | — | Open ≥ 40 % | Ziel: Support-Tickets „wo ist mein Paket“ < 5 % der Bestellungen, Chargebacks 0 → sonst Text ändern, nie streichen |
| post_delivery Content | $0,47 je Flow (3–5 Mails) | $0,10; Cross-Sell/Code: $0,40 | ≥ 1,5 % | Content-Mail 2× in Folge unter Schwelle → in den „warm“-Pfad verschieben (nur Klickerinnen) statt löschen |
| winback | $0,07–0,84 | $0,05 | ≥ 1 % | Mail 4/5 raus, wenn Reaktivierung (Placed Order in 30 d nach Mail) < 0,3 % |
| sunset | kein Umsatz-Ziel | — | Klick „stay“ ≥ 3 % | Suppression-Quote melden, nicht bewerten |

Abschalten heißt: Mail auf `status: disabled` (PATCH flow-action; kein recreate nötig) — Text wird umgeschrieben (2 Autoren + 1 Richter) und als A/B-Variante zurückgeholt; erst zwei Runden unter Schwelle = endgültig raus.
Immer, unabhängig vom RPR: Unsubscribe > 0,2 % oder Spam > 0,1 % je Mail → sofort `disabled` (30-tage-Spec §5.9, Quelle 7).

## 6. Lücke zur heutigen Spec — was bleibt, was neu ist, was das Skript braucht, Bau-Reihenfolge

**Bleibt:** alle 45 Mails der 30-tage-Spec (Keys, Texte, A/B-Varianten, Delays 07:00, Smart-Sending-Liste `NO_SMART`, Flow-Filter). **Neu:** 9 Conditional-Splits, 2 Trigger-Splits, 4 Absichts-Filter, Kappe auf 31 Mails, VIP-Flow entfällt (wird Pfad), `recreate --draft`.

### 6a. Skript-Erweiterung `bin/klaviyo.py` (drei Änderungen, kleinster Diff)

**(1) `additional_filters` je Mail** — Feld existiert in `send()` (`"additional_filters": None`). Spec-Feld `filters` je Mail in `state/flows-*.json` oder Konstante `MAILFILTER = {key: [cond, …]}`; gleiche Condition-Form wie `filters()`. Kappe als Default für alle Keys, die nicht in `NO_SMART` sind:
```json
"additional_filters": {"condition_groups": [
  {"conditions": [{"type": "profile-metric", "metric_id": "<Received Email>", "measurement": "count",
                   "measurement_filter": {"type": "numeric", "operator": "less-than-or-equal", "value": 2},
                   "timeframe_filter": {"type": "date", "operator": "in-the-last", "quantity": 7, "unit": "day"}}]},
  {"conditions": [{"type": "profile-metric", "metric_id": "<Clicked Email>", "measurement": "count",
                   "measurement_filter": {"type": "numeric", "operator": "greater-than-or-equal", "value": 1},
                   "timeframe_filter": {"type": "date", "operator": "flow-start"}}]}
]}
```
(Gruppen = UND, innerhalb = ODER — api-research Z. 96. Für „Klick ODER Viewed Product“ beide Bedingungen in EINE Gruppe.) Metrik „Received Email“ und „Clicked Email“ in `METRICS` aufnehmen; `check` zeigt, ob sie im Konto existieren.

**(2) `conditional-split` im PLAN** — neue Schrittform `("split", NAME, [Bedingungen], [Schritte JA], [Schritte NEIN])`; `flow()` baut daraus:
```json
{"temporary_id": "s4", "type": "conditional-split", "links": {"next_if_true": "d_wieder0", "next_if_false": "d_erst0"},
 "data": {"profile_filter": {"condition_groups": [{"conditions": [
   {"type": "profile-metric", "metric_id": "<Placed Order>", "measurement": "count",
    "measurement_filter": {"type": "numeric", "operator": "greater-than-or-equal", "value": 2},
    "timeframe_filter": {"type": "date", "operator": "alltime"}}]}]}}}
```
Beispiel PLAN-Eintrag post_delivery (kumulierte Delays wie heute, `UNTIL` 07:00):
```python
"post_delivery": (("metric", "Fulfilled Order"),
  [(3,"days","post_purchase-transit",UNTIL), (4,"days","post_delivery-arriving",UNTIL), (4,"days","post_delivery-arrived",UNTIL),
   ("split", "wieder", [("Placed Order","greater-than-or-equal",2,{"type":"date","operator":"alltime"})],
     [(7,"days","post_purchase-3",UNTIL), (2,"days","vip-1",UNTIL), (8,"days","vip-2",UNTIL), (17,"days","vip-3",UNTIL), (15,"days","post_delivery-newin",UNTIL)],
     [(3,"days","post_purchase-2",UNTIL), (4,"days","post_purchase-3",UNTIL), (6,"days","post_delivery-crosssell",UNTIL), (3,"days","post_delivery-code2",UNTIL),
      ("split", "warm", [("Clicked Email","greater-than-or-equal",1,{"type":"date","operator":"flow-start"})],
        [(6,"days","post_delivery-ugc",UNTIL), (5,"days","post_delivery-style",UNTIL), (7,"days","post_delivery-vip",UNTIL), (7,"days","post_delivery-season",UNTIL), (8,"days","post_delivery-newin",UNTIL)],
        [(18,"days","post_delivery-vip",UNTIL), (15,"days","post_delivery-newin",UNTIL)])])],
  ["Placed Order","Cancelled Order","Refunded Order"], {"duration": 0, "unit": "alltime"}),
```
Ein Mail-Key darf in zwei Pfaden stehen (post_delivery-vip, -newin, post_purchase-3) → Template einmal, zwei send-Actions mit eigener `temporary_id` (`m<pfad><i>`); `summary()`/`plan.json` zeigen den Baum eingerückt. Klaviyo-Falle (Quelle 3): Engagement-Split nie direkt hinter einer Mail — im Baum steht vor S2/S5/S7 immer ≥ 2 Tage Delay ✅.

**(3) `recreate --draft`** — heute: alter Flow → draft, neuer → live, alter gelöscht (Z. 281–294). Neu: mit `--draft` bleibt der alte live, der neue bleibt `draft`, nichts wird gelöscht, `ids.json` merkt `pending`; `klaviyo.py go [--flows]` = neuer live → alter draft → alter löschen. Das ist sein „Entwurf … wenn ich go sage“.

**Nicht per Skript (Schema nicht belegt, developers.klaviyo.com heute 403):** `trigger-split` (T1/T2 `$value ≥ 150`) und Segment-Trigger (sunset). Weg wie Klaviyo empfiehlt (api-research Z. 100): einmal im UI bauen → `GET /api/flows/{id}?additional-fields[flow]=definition` → Schema lesen → ins Skript übernehmen. Bis dahin: cart/checkout wie heute live lassen (unverändert, kein Risiko), T1/T2 Montag im UI.

### 6b. Bau-Reihenfolge

| Schritt | Wann | Was | Wer |
|---|---|---|---|
| 1 | heute | Skript: (1) `additional_filters` + Kappe, (2) `conditional-split`, (3) `recreate --draft`; `--selftest`: `plan` für welcome/post_delivery/winback ohne Key, Baum in `plan.json` sichtbar, `grep DESCRIPTOR 04-output/flows/*.html` leer | arbeiter |
| 2 | heute | Texte: 5 neue Mails der 30-tage-Spec (welcome-1b/-6/-7, pd-style/-season) + vip-1..3 + winback-5 + sunset-2 = 11 Mails, je 2 Autoren + 1 Richter; Varianten „Kundin“ für welcome/browse Mail 1 (ohne „first order“) | urteil |
| 3 | heute | `flows.py build --klaviyo --no-proof` → HTML ansehen → `klaviyo.py recreate --draft --flows welcome,post_delivery,winback` → **Entwurf in Klaviyo, Screenshot je Baum an ihn** | Sitzung |
| 4 | Mo | UI: cart/checkout je ein Trigger-Split `$value ≥ 150` (Pfad „heiß“ = co4-2/ca4-2 mit 2 Codes), sunset-Segment + Flow; GET-Definition → Schema ins Skript | Sitzung (Chrome) |
| 5 | Mo, nach seinem „go“ | `klaviyo.py go` → welcome/post_delivery/winback live; cart/checkout heiß live; `abreport` Woche 1 als Nullmessung | Sitzung |
| 6 | So (weekly) | `abreport` → `waste.json` → Ampel je Mail (§5) → Telegram-Zeile je roter Mail; Gewinner der A/B-Welle 1 werden Basis (ab-roadmap) | handgriff + urteil |
| 7 | nach `bin/go.sh` (sein Klick, Onsite-JS) | browse-Split S3 + Absichts-Filter „Viewed Product“ in cart; Back-in-stock-Flow (Theme-Knopf) | arbeiter |

## 7. Pre-Mortem (Mail-Sequenz = Sichtbarkeit) — 5 Gründe, warum es scheitert, je mit Prüfung vorher

1. **Klaviyo lehnt die Definition ab** (`conditional-split`-Schema aus dem Brief vom 13.09., heute nicht gegenprüfbar: 403; `Received Email` heißt im Konto anders; `alltime`-timeframe braucht ein anderes Objekt) → Prüfung: erst `recreate --draft --flows winback` (kleinster Baum, 2 Splits), Fehlertext lesen; parallel im UI einen Mini-Flow mit einem Split bauen und per GET das Schema vergleichen, bevor welcome/post_delivery folgen.
2. **Ein Mail-Filter wirft die Frau aus dem Flow statt die Mail zu überspringen** (wenn Klaviyo `additional_filters` wie Flow-Filter behandelt) → Prüfung: Testprofil (eigene Adresse) durch winback-Entwurf mit Kappe 0 schicken (Flow „manual“), in der Flow-Analytics muss „Skipped: filters“ an der Mail stehen und die nächste Mail trotzdem geplant sein; sonst Kappe nur als Smart Sending, Absichts-Filter als Split.
3. **Engagement-Splits sortieren alle in „kalt“, weil Klicks über Apple/Gmail-Proxys nicht als Klick zählen oder die Frau nur geöffnet hat** (Quelle 3/14: Timing; MPP) → Prüfung: nach 7 Tagen `abreport`: Anteil „JA“ an S2/S5 muss ≥ 25 % sein (Welcome-Klick 9,2 % je Mail × 3 Mails, Quelle 8); liegt er < 10 %, Bedingung auf „Clicked ∨ Opened ≥ 2“ weiten.
4. **Kappe + Smart Sending + Kampagnen löschen die Kette still** (Frau bekommt in Woche 1 zwei Kampagnen → welcome-2 und -6 übersprungen → Sequenz ohne Beweis und Wahl) → Prüfung: Kampagnen-Plan der Woche neben den Tagesraster legen; Kampagnen-Segment schließt „in welcome < 7 d“ und „PP 0–14“ aus (30-tage-Spec §5.8); `abreport` zeigt Skipped-Zahl je Mail — > 30 % = Kappe auf 3.
5. **Zwei send-Actions mit demselben Key (post_delivery-vip in „warm“ und „kalt“) machen A/B-Tests und `abreport` doppelt/unlesbar** → Prüfung: `plan.json` je Action eindeutige `name` (`Post-Delivery #9 warm`/`#9 kalt`), `abreport` gruppiert nach `flow_message_id`, nicht nach Key; Selftest prüft, dass keine `temporary_id` doppelt ist.

**Bewertung:** Der Baum liegt innerhalb dessen, was Quellen 1–8 als Standard beschreiben (3 Achsen: Kaufhistorie, Wert, Klick), nutzt keine Daten, die wir nicht haben, und senkt die Mailzahl je Frau statt sie zu heben —
das ist die Praxis der 8-stelligen Marken (−24 % bis −44 % Sendungen bei steigendem Umsatz). **Empfehlung:** heute Skript-Erweiterung (1)–(3) + 11 Texte + Entwurf für welcome/post_delivery/winback; cart/checkout unverändert live lassen, bis der
Trigger-Split im UI steht (Montag); sein „go“ schaltet, `abreport` entscheidet ab 500 Empfängerinnen je Mail, was verschwendet ist.

## 8. Offene Fragen an ihn (nur Geld/Sichtbarkeit)

1. **Heißer Checkout ≥ $150 mit 2 Codes ab Mail 2 (NL15-Pool + SHIP-Pool)** — a) ja, ab Mail 2 ← empfohlen (deine Antwort 5) · b) erst Mail 3 · c) Schwelle anders als $150
2. **Wiederkäuferin bekommt keinen Rabatt-Code mehr** (post_delivery „wieder“, winback „wieder“ nur SHIP-Pool) — a) ja ← empfohlen (Marge, Quellen 5/11) · b) NL15-Pool auch für sie
3. **Live-Schaltung** — a) Montag nach deinem Blick auf die 3 Entwurfs-Bäume (Screenshots) ← empfohlen · b) sofort nach Entwurf (rules 16.09. „keine Rückfragen für Klaviyo“) — Entwurf ist dein Wort von heute, deshalb a
