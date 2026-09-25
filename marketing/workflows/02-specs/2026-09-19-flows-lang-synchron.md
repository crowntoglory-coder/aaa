# Spec: Flows lang + synchron — Post-Purchase mit Rabatt, Chargeback-Schutz, Lifecycle (19.09.2026)

Seine Ansage 19.09. 14:10 (rules.md §Seine Ansagen 19.09. ~14:10): „nachdem ein kunde gekauft hat … nochmal emails … direkt für post purchase mit
rabatt oder so und auch emails für kundenzufriedenheit um chargeback zu minimieren … alle email flows … lange sequenzen … smart … effizient …
richtig synchronisiert … cb low und profit maxx per customer.“ Rolle: Spec (urteil). Baut: arbeiter. Kein Klaviyo-Schreibzugriff hier.
Gelesen: marketing/CONTEXT.md · 04-output/2026-09-15-klaviyo-setup.md · state/flows-{v2,seq,post2,winback4-sunset,cart4,checkout4,welcome45,browse}.json ·
rules.md §Mails/§Rabattcodes/§Cashflow · funnel.md §2 · email-cro.md §2/§4/§7 · psychologie.md §5/§8 · bin/{flows,klaviyo,coupons}.py · api-research.md.

## 1. Ist-Karte (7 Flows, 26 Mails live + 2 gebaut) — Stand `bin/klaviyo.py` PLAN + `state/klaviyo/ids.json`

| Flow (ID) | Trigger | Nr · Key | Tag/Std nach Trigger | Zweck | Rabatt | Filter / Wiedereintritt |
|---|---|---|---|---|---|---|
| welcome `UrZTxm` | Liste | 1 welcome · 2 welcome-2 · 3 welcome-3 (Text) · 4 welcome-4 · 5 welcome-5 | 0 · +3 d · +7 d · +10 d · +14 d | Code einlösen, Render-Einwand, Risk Reversal, Sale-Logik, Größen-Guide | WELCOME15 (alle 5) | Placed Order = 0 seit Start · nie |
| browse `VbMWDm` | Viewed Product | 1 browse · 2 browse-2 · 3 browse-3 | +1 h · +25 h · +73 h | Teil + Detail, Alternativen, vier in der Palette | WELCOME15 (nur Mail 1) | Placed Order, Added to Cart, Checkout Started = 0 · 7 d |
| cart `VyLYvs` | Added to Cart | 1 ca4-1 · 2 ca4-2 (Text) · 3 ca4-3 · 4 ca4-4 | +1 h · +25 h · +49 h · +73 h | Größe da, Claire + Code, Code groß, letzte Mail | Pool NL15 ab Mail 2 (96 h), SHIP ab Mail 4 (48 h) | Placed Order, Checkout Started = 0 · 7 d |
| checkout `SiyuWy` | Checkout Started | 1 co4-1 · 2 co4-2 (Text) · 3 co4-3 · 4 co4-4 | +75 min · +25 h · +49 h · +73 h | wie Cart, Warenkorb dynamisch, Countdown | Pool NL15 ab Mail 2, SHIP Mail 4 | Placed Order = 0 · 7 d |
| post_purchase `RMPWLq` | Placed Order | 1 post_purchase | 0 min | Dank, Größe prüfen, 7–10 Tage, support@ | — | kein Filter · jede Bestellung |
| post_delivery `UjtpcY` | Fulfilled Order | 2 post_purchase-transit · 3 post_purchase-2 · 4 post_purchase-3 · 5 post_delivery-crosssell · 6 post_delivery-ugc · 7 post_delivery-vip (Text) | +3 d · +10 d · +14 d · +21 d · +30 d · +45 d | unterwegs/Tracking/Abrechnungsname · Wear+Care · Passform-Bitte · zweites Teil · Foto · zweite Bestellung | — (Versand ab $150 als Anreiz) | kein Filter · jede Bestellung |
| winback `Th44Xv` | Placed Order | 1 winback · 2 winback-2 · 3 winback-3 (Text) · 4 winback-4 (Text, gebaut, nicht live) | +90 d · +97 d · +104 d · +118 d | Neuheiten, Looks, letzte Sale-Mail, New In ohne Frist | — (45 % Sale im Preis) | Placed Order = 0 seit Start · jede Bestellung |
| sunset (kein Flow) | Segment (fehlt in PLAN) | 1 sunset (Text) | einmalig, 14 d Frist | Re-Permission, ?stay=1 | — | Placed Order = 0 in 90 d (im Segment) |

**Lücken (Ist):**
1. **Tag 0 → Versand (1–3 d) → Zustellung (7–10 d) = bis 13 Tage, in denen nur eine Mail (Tag 0) und die Transit-Mail (Versand +3) kommen.** Kein „was passiert jetzt“ am Tag 1, keine
   Verzögerungs-Mail, wenn nach Tag 5 noch nichts verschickt ist (Transit verspricht „Running late — we write first“, aber niemand schreibt), keine „kommt jetzt an“-Mail, **keine
   „angekommen? passt alles?“-Mail** nach dem Fenster. Genau dort entstehen „item not received“ (32 % der Friendly-Fraud-Fälle, chargeflow 2026) und „not as described“.
2. **Abrechnungsname unbelegt.** Transit-Mail behauptet „NORA LANELLE or Northbound Systems LLC“; Setup-Doc 15.09. sagt: Descriptor nie nachgesehen. Lesen per API scheitert
   (`shopifyPaymentsAccount.chargeStatementDescriptor` → „Access denied … read_shopify_payments_accounts“, geprüft 19.09.). „Unrecognized charge“ = 26 % der Chargebacks (ClearlyPayments 06/2024);
   „unrecognized entries spark customer disputes 27 % of the time“, 58 % finden Descriptoren verwirrend (Shopify Enterprise Blog 08.08.2025).
3. **Kein Rabatt nach dem Kauf** (rules 15.09. „Kombination, nicht Rabatt“) — seine Ansage 19.09. sagt „mit rabatt oder so“ und ist jünger. Cross-Sell Tag 21 ohne Code, VIP Tag 45 ohne Code.
4. **Loch Tag 45–90**: nach der VIP-Mail 45 Tage Stille bis Winback. **Sunset** hat keinen PLAN-Eintrag (Segment-Trigger fehlt im Skript).
5. **Keine Synchronisation Post-Purchase ↔ Browse/Cart**: Käuferin, die am Tag 3 stöbert, bekommt browse-1 mit WELCOME15 (Erstkunden-Code, den sie nicht mehr einlösen kann).
   Kein Stopp der Post-Delivery-Kette bei Storno/Erstattung (Metriken Cancelled/Refunded Order nicht im Filter). Keine Kampagnen-Sperre in Tagen 0–14. Kein Sendefenster (Delays landen zur Bestell-Uhrzeit).
6. Mails, die Zufriedenheit tragen, sind „Marketing“: Smart Sending überspringt Follow-ups, wenn 16 h vorher eine Kampagne kam — für die Chargeback-Mails darf das nicht passieren.
7. Konflikt (nur notiert, nicht Teil dieser Spec): marketing/CONTEXT.md „kein ‚45 % off‘ in Mails“ vs. winback-2/-3, welcome „45 %“-Texte. Klärt die nächste Winback-Runde.

## 2. Soll-Karte „Customer Lifecycle“ (ein Bild)

    Anmeldung ─ welcome 1–5 (0/3/7/10/14 d, WELCOME15) ──┐
    Ansehen ─── browse 1–3 (1/25/73 h) ─────────────────┤  Kauf beendet alle drei (Placed Order = 0 seit Start, je Schritt geprüft)
    Warenkorb ─ cart 1–4 · checkout 1–4 (1 h … 73 h) ────┘
                     │ PLACED ORDER
    post_purchase ── PP1 Dank 0 min · PP2 „was jetzt passiert“ +24 h · PP3 „noch nicht verschickt“ +5 d (nur wenn unversendet)
                     │ FULFILLED ORDER (Tag 1–3)
    post_delivery ── PD1 Transit +3 · PD2 „kommt jetzt an“ +7 · PD3 „angekommen? passt?“ +11 · PD4 Wear+Care +14 · PD5 Passform/Review +18
                     · PD6 zweites Teil MIT CODE +24 · PD7 Code endet +27 · PD8 Foto +33 · PD9 Kombination (Claire) +45 · PD10 New In +60
                     │ 90 d ohne Bestellung          │ jede neue Bestellung → PD-Kette stoppt, neue Kette startet
    winback 1–4 (90/97/104/118 d) ── 90 d ohne Open/Klick/Kauf ── sunset (einmalig, 14-d-Frist) ── Suppression

Pre-Purchase bleibt wie im Ist (Welle-1-Tests laufen); nur der Browse-Filter ändert sich (§4). Timing Post-Delivery relativ zu **Fulfilled Order**, Sendefenster 07:00 Ortszeit
der Kundin für alle Tages-Delays (`timezone: profile` + `delay_until_time`; Omnisend: Fr 7 Uhr beste Conversion, GetResponse: Opens 4–6 h, email-cro §2). Stunden-Delays (Cart/Checkout) unverändert.

### 2a. post_purchase (Trigger Placed Order · Wiedereintritt jede Bestellung · Filter: Fulfilled Order = 0 seit Start → Kette endet still, sobald verschickt)

| Nr · Key | Timing | Zweck (ein Satz) | Kernbotschaft | Rabatt | Messgröße | Status |
|---|---|---|---|---|---|---|
| 1 post_purchase | 0 min, Smart Sending aus | Bestätigen, dass sie richtig gewählt hat; nichts verkaufen. | Danke; Größe heute gegen den Guide halten; 7–10 Tage ab Versand; Abrechnungsname; support@ | — | Öffnung, Support-Mails „Größe“ vor Versand | **umtexten**: Looks-Block raus (rules Hero + ein Block), Zeile „On your card statement it reads [DESCRIPTOR]“, CTA → `{{ event.extra.order_status_url }}` statt /account |
| 2 post_purchase-next | +24 h, 07:00 | Erwartung setzen, bevor sie fragt. | Was jetzt passiert: gepackt in 1–3 Tagen, dann 7–10 Tage; Tracking kommt per Mail; „nothing to do on your side“; Abrechnungsname; support@, 1–2 Werktage | — | Support-Tickets „where is my order“ je 100 Bestellungen | **neu** |
| 3 post_purchase-wait | +4 d (Tag 5), 07:00 | Verzögerung selbst melden, bevor sie zur Bank geht. | „Still being prepared — we said we'd write first“; neues Fenster; warten oder volle Erstattung, ihre Wahl; support@ | — | Anteil Bestellungen, die Tag 5 erreichen; Chargebacks „not received“ | **neu** — sendet nur, wenn Filter (unversendet) noch gilt |

### 2b. post_delivery (Trigger Fulfilled Order · Wiedereintritt jede Bestellung · Filter: Placed Order = 0 seit Start, Cancelled Order = 0, Refunded Order = 0)

| Nr · Key | Timing (kum.) | Zweck | Kernbotschaft | Rabatt | Messgröße | Status |
|---|---|---|---|---|---|---|
| 1 post_purchase-transit | +3 d, Smart Sending aus | Halbzeit: wo es ist, wie lange noch. | 3 Tage unterwegs, 4–7 to go; Tracking; „running late — we write first“; Rückgabe statt Bank; Abrechnungsname | — | Klicks Tracking | bestehend; Descriptor-Zeile auf belegten Wert |
| 2 post_delivery-arriving | +7 d, 07:00 | Ankunft ankündigen, Fenster benennen. | „Any day now“ (Tag 7–10 ab Versand); was tun, wenn es da ist: anprobieren, 30 Tage laufen ab Zustellung; **nichts bis Tag 10? schreib uns, nicht der Bank** | — | Support-Tickets „late“ Tag 8–12 | **neu** |
| 3 post_delivery-arrived | +11 d, 07:00, Smart Sending aus | Der eine Check-in, der Chargebacks abfängt. | „Did it land? Fit right? Anything off — one mail to support@, sorted in 1–2 business days, easy returns 30 days. Before you call your bank.“ Ein Knopf (Kontaktseite/mailto) | — | Chargeback-Rate (Disputes/Orders), Retouren-Quote, Antworten | **neu** — mit Track123 später Trigger „Delivered Shipment“ +1 d |
| 4 post_purchase-2 | +14 d | Tragen statt zurückschicken. | Drei Arten zu tragen; Pflege; Rückgabe 30 Tage ab Zustellung | — | Retouren-Quote | bestehend, +10 → +14 (war vor Zustellung bei Verzug) |
| 5 post_purchase-3 | +18 d | Passform-Stimme einsammeln (Review 7–10 d nach Zustellung, email-cro §2). | Größe, Körpergröße, true/roomy an support@, Betreff „Fit“ | — | Antworten je 100 | bestehend, +14 → +18 |
| 6 post_delivery-crosssell | +24 d, 07:00 | Zweite Bestellung — Kaufpaar zum gekauften Teil, jetzt mit Code. | Mantel → Strick/Hose, Kleid → Mantel; **Code 15 %, 4 Tage** (Pool `{% coupon_code 'CHECKOUT15' %}` = NL15-MMDD, 96 h — Wert existiert, kein neuer; Kundin sieht nur NL15-…); Versand ab $150 | ja (1a/1b/1c, **braucht sein ok**) | Zweitkauf-Rate 30 d, RPR | bestehend, +21 → +24, Code-Block neu |
| 7 post_delivery-code2 | +27 d, Text, Claire | Frist wahr aussprechen. | „Your code ends tomorrow“ (96 h ab Tag 24 = Tag 28); gleiche Paare, ein Link; kein Druck-Vokabular | ja (derselbe Code) | Zweitkauf-Rate Tag 27–28 | **neu** — nur wenn 1a/1b |
| 8 post_delivery-ugc | +33 d | Foto im Teil. | Spiegel-Selfie an support@ oder @noralanelle | — | Fotos je 100 | bestehend, +30 → +33 |
| 9 post_delivery-vip | +45 d, Text | Kombination zum gekauften Teil, Passform bekannt. | Drei Teile einer Palette, gleiche Größe, Versand ab $150/$250 | — | Zweitkauf-Rate 60 d | bestehend |
| 10 post_delivery-newin | +60 d, 07:00 | Lebenszeichen vor Winback, kein Rabatt. | New In in ihrer Palette; 7–10 Tage; easy returns; keine Frist | — | Klicks New In | **neu** (schließt Loch 45–90) |

### 2c. winback (Placed Order +90 d · Filter Placed Order = 0 seit Start) und sunset

winback 1–4 bleiben (90/97/104/118 d; Mail 4 live schalten). Kein Rabatt-Nachschlag: Rückkauf-Rabatt liegt in PD6/7 (Tag 24–28 nach Versand), Winback führt über Neuheit (funnel §2).
sunset: Segment „Opened = 0 ∧ Clicked = 0 ∧ Placed Order = 0 in 90 d ∧ Profil > 90 d ∧ ≥ 3 Mails erhalten“ → eine Mail → 14 d → kein Klick → Suppression. Käuferinnen der
letzten 90 Tage sind per Segment draußen; wer in post_delivery oder winback steckt, ist damit automatisch draußen (beide enden vor Tag 90 ohne Kauf → dann erst Sunset-fähig).

## 3. Chargeback-Schutz als Querschnitt

| Ursache (Anteil) | Fängt ab | Warum das wirkt (Beleg) |
|---|---|---|
| **Unrecognized charge** (26 %, ClearlyPayments 06/2024; 27 % Disputes bei verwirrendem Descriptor, Shopify 08/2025) | PP1, PP2, PD1: Zeile „On your card statement it reads [DESCRIPTOR] — that's us“ | Sie erkennt die Buchung, bevor die Bank-App sie fragt „Do you recognize this?“ |
| **Item not received** (32 % der Friendly-Fraud-Fälle, chargeflow 2026; bis 20 % Retail, ClearlyPayments) | PP2 (Fenster), PP3 (Verzug selbst melden), PD1/PD2 (Tracking, „nothing by day 10 → write us“), PD3 (Check-in) | Klaviyo/Shopify: „Detailed receipts and live tracking updates provide customers with proof and peace of mind“ (Shopify 08/2025); „item arrives after the agreed-upon delivery date → customer must attempt to return before initiating a chargeback“ (ebd.) — nur wenn ein Datum genannt war |
| **Not as described / Passform** (Produkt-Issues 24 %, ClearlyPayments; 64 % der Kleidungs-Retouren = Passform, PowerReviews) | PP1 (Größe vor Versand prüfen), PD3 („fit right? easy returns“), PD4 (tragen), Render-Erwartung aus welcome-2 | Rückgabe ist der leichtere Weg als die Bank, wenn er in der Mail steht (psychologie §5: Rückgabe sichtbar → Kauf +, Streit −) |
| **Betrugsverdacht neue Marke, Meta-Traffic** | PP1/PP2 Absender support@nora-lanelle.com, Firmenadresse im Fuß (CAN-SPAM), US brand/Wyoming, Klaviyo-Absenderdomain (offen bei ihm) | Cialdini Autorität/Konsistenz: dieselbe Adresse, derselbe Name in jeder Mail; „easy-to-find customer support“ (Shopify 08/2025) |
| **Abo-/Doppelbuchungsangst** | PP2 „one order, one charge, nothing recurring“ | Billing errors 5–10 % (ClearlyPayments) — ein Satz reicht |

Regeln in jeder Post-Purchase-Mail: support@nora-lanelle.com sichtbar (Link/mailto, nie „reply to this email“); „easy returns“, nie „free returns“; keine Streichpreise, kein „45 % off“;
keine erfundenen Stimmen (`--no-proof`); Rabatt nur mit existierendem Code; Founder-Text = „Claire, Nora Lanelle“, Design-Mails „Nora Lanelle“.

## 4. Synchronisation — als Klaviyo-Bedingungen, die `bin/klaviyo.py recreate` anlegt (oder anlegen müsste)

| Regel | Klaviyo-Formulierung | Skript heute |
|---|---|---|
| Kauf beendet Cart/Checkout/Browse/Welcome | Flow-Filter `Placed Order = 0 since flow-start` (Klaviyo prüft vor jedem Schritt) | ✅ PLAN `filt` |
| Käuferin (14 d) bekommt keine Browse-Mail (WELCOME15 = Erstkunden-Code) | Browse-Filter zusätzlich `Placed Order = 0 in the last 14 days` | ❌ **Erweiterung 1**: `filt`-Einträge als Tupel `(metric, operator, value, timeframe)`; `timeframe_filter {"type":"date","operator":"in-the-last","quantity":14,"unit":"day"}` (api-research Z. 96); Cart/Checkout bewusst offen (echte Zweitkauf-Absicht, Code passt) |
| post_purchase endet, sobald verschickt | Flow-Filter `Fulfilled Order = 0 since flow-start` | ✅ (Metrik in METRICS) |
| Storno/Erstattung stoppt Post-Delivery (auch Zweitkauf-Code) | Flow-Filter `Cancelled Order = 0` ∧ `Refunded Order = 0 since flow-start` | ❌ **Erweiterung 2**: METRICS += Cancelled Order, Refunded Order, Delivered Shipment; in `apply()`: fehlt eine Filter-Metrik → nur den Filter weglassen + Warnung, nicht den ganzen Flow überspringen (heute: Flow wird übersprungen) |
| Neue Bestellung startet die Post-Delivery-Kette neu, alte stoppt | Wiedereintritt `alltime/0` + Flow-Filter `Placed Order = 0 since flow-start` | ✅ Wiedereintritt · Filter = Erweiterung 1 (Standardfall bleibt kompatibel) |
| Chargeback-Ereignis | gibt es in Klaviyo nicht; Proxy = Refunded/Cancelled Order; echte Disputes von Hand: Profil-Eigenschaft `dispute=true` → Filter | ❌ später: `klaviyo.py flag EMAIL` (PATCH /api/profiles) — nicht Teil dieses Baus |
| Sendefenster 07:00 Ortszeit für Tages-Delays | `time-delay` mit `timezone: "profile"`, `delay_until_time: "07:00"` | ❌ **Erweiterung 3**: PLAN-Schritt optionales 4. Feld `until` → `delay_until_time` (Format gegen Spec prüfen) |
| Frequenz-Deckel | Smart Sending 16 h an für alle Follow-ups; **aus** für PP1, PD1, PD3 (Service, darf nie übersprungen werden) und Cart/Checkout Mail 1 | ⚠️ **Erweiterung 4**: Spec-Feld `"smart_sending": false` je Mail statt Hardcode-Tuple `NO_SMART` |
| Kampagnen-Sperre Tage 0–14 nach Kauf | Segment `Placed Order ≥ 1 in the last 14 days` → in jeder Kampagne als Ausschluss (UI, Kampagnen gehen von Hand) | ❌ **Erweiterung 5**: `klaviyo.py segment NAME` (POST /api/segments) legt „PP 0–14“ und das Sunset-Segment an |
| Sunset-Trigger | Trigger `{"type":"segment","id":…}` | ❌ **Erweiterung 5**: PLAN kennt `("segment", name)`; Mail „sunset“ liegt in flows-winback4-sunset.json |
| Winback nicht während Post-Delivery | Winback startet Tag 90, Post-Delivery endet Tag 60+3 — keine Überlappung; Winback-Filter Placed Order = 0 seit Start | ✅ |
| Welcome nicht für Käuferin | Welcome-Filter Placed Order = 0 seit Start | ✅ |
| Quiet Hours | Klaviyo hat sie nur für SMS; für Mail = Sendefenster oben; keine Nacht-Sends, weil alle Tages-Delays auf 07:00 laufen; Stunden-Mails (Cart/Checkout) folgen der Handlung | — |

Reihenfolge der Flow-Priorität, wenn eine Frau in mehrere passt: post_purchase > post_delivery > checkout > cart > browse > welcome > winback > sunset — umgesetzt über die Filter oben, nicht über eine Klaviyo-Einstellung (gibt es nicht).

## 5. Profit je Kundin — Rechnung mit Annahmen (alle Annahmen markiert)

- AOV **$150** (Annahme; TIER `bin/reprice.py`: 69 Preise, Ø $132,7, Spanne $49–269; Schwelle $150 = Versand frei zieht Zweiteiler). Marge: `serve.calc` MARGIN_MIN = 0,60 → Landed ≤ $60, **GPT ≈ $90** vor Gebühren, ≈ **$85** nach Shopify Payments (2,9 % + 30 ¢, Annahme US-Standardsatz).
- **Zweiter Kauf** zu $150 mit 15 % Code: Netto $127,50 − Landed $60 − Gebühr $4 ≈ **$63 GPT**; ohne Code ≈ $85. Wiederkaufrate Basis **15–19 %** (BS&Co 18,8 % über 156k Kundinnen; DTC-Fashion 15–17 %, Foundry CRO 2026 — beide Vendor-Zahlen).
  Jeder Punkt Wiederkaufrate = +$0,63 je Kundin (mit Code) bzw. +$0,85 (ohne). Ziel dieser Sequenz: +5 Punkte → **+$3–4 je Kundin**, bei 1.000 Kundinnen/Monat +$3.000–4.000 GPT. Ob der Code die 5 Punkte bringt oder nur Marge kostet, sagt der A/B-Test PD6 (Code vs. Versand).
- **Vermiedener Chargeback**: $15 Gebühr (Shopify Payments US; bei Gewinn rückerstattet, Help Center) + Ware $60 Landed weg + Umsatz $150 weg ≈ **$165 direkt**; ClearlyPayments (06/2024, eigene Zahl): „for every $1 in chargebacks … $2.40“ → $360.
  Ratio-Risiko: Visa VAMP ab 06/2025 Acquirer „above standard“ 0,5 %, „excessive“ 0,7 %; Händler „excessive“ 2,2 % → **1,5 % ab 04/2026** (Ravelin, Stand 01/2026); Mastercard ECP 1,5 % + 100 Fälle. Bei 1.000 Bestellungen/Monat sind 5 Disputes = 0,5 % — der Acquirer wird nervös, lange bevor Visa den Händler trifft.
- Folge für die Reihenfolge: **ein vermiedener Chargeback ($165–360) wiegt 2–4 zweite Käufe ($63–85)** → die Service-Mails (PP2, PP3, PD2, PD3) werden zuerst gebaut und zuerst live geschaltet; der Code kommt danach.

## 6. Bauplan

**Neue Mails, in Baureihenfolge** (Skelett `state/flows-postpurchase-lang.json`, nur die neuen Keys; bestehende bleiben in ihren Specs):

| # | Key · Flow · Nr | Timing | Kurz-Brief | Rabatt | A/B-Hypothese „because …“ |
|---|---|---|---|---|---|
| 1 | post_delivery-arrived · post_delivery · 3 | Fulfilled +11 d, 07:00, Smart Sending aus | Ein Check-in nach dem Fenster: angekommen, passt, sonst support@ vor der Bank. Format E (Text-Hero + steps), ein Knopf. | — | B „Claire, persönlich“ schlägt A „Nora Lanelle, Service“ bei Antworten, because eine Person fragt, keine Marke (psychologie §2 Sympathie) |
| 2 | post_purchase-next · post_purchase · 2 | Placed +24 h, 07:00 | Was jetzt passiert: 1–3 d packen, 7–10 d Weg, Tracking kommt, eine Buchung, Abrechnungsname, support@. Format B (steps, kein Bild). | — | B mit Zeitstrahl-Grafik (steps) schlägt A Fließtext bei Support-Tickets „where is my order“, because Zeitstrahl ist in 9 s lesbar (psychologie §8.10) |
| 3 | post_delivery-arriving · post_delivery · 2 | Fulfilled +7 d, 07:00 | „Any day now“: Fenster, was am Tag der Zustellung zu tun ist, 30 Tage ab Zustellung, nichts bis Tag 10 → schreiben. | — | B Betreff mit Zahl („Day 7 of 10“) schlägt A („Nearly there“), because Zahl setzt die Erwartung exakt (email-cro §7.2) |
| 4 | post_purchase-wait · post_purchase · 3 | Placed +4 d, 07:00, nur unversendet | Verzug selbst melden: neues Fenster, warten oder Erstattung, ihre Wahl. Text, Claire. | — | B mit Erstattungs-Angebot vorn schlägt A (Fenster vorn) bei Chargebacks, because die Wahl nimmt den Bank-Weg weg (Risk Reversal, psychologie §4) |
| 5 | post_delivery-code2 · post_delivery · 7 | Fulfilled +27 d, Text, Claire | Code endet morgen; dieselben Paare; ein Link. | Pool NL15 | B „Fakten“ (Frist + Betrag) schlägt A „persönlich“, because eine wahre Frist trägt sich selbst (funnel §5) |
| 6 | post_delivery-newin · post_delivery · 10 | Fulfilled +60 d, 07:00 | New In in ihrer Palette, keine Frist, kein Code. Format D (split + grid4). | — | B „Kombination zum gekauften Teil“ schlägt A „New In gesamt“ bei Klicks, because Relevanz zum Besitz (Winback-4-Logik) |

**Bestehende Mails ändern:** post_purchase (Looks raus, Descriptor-Zeile, CTA order_status_url) · post_purchase-transit (Descriptor-Zeile auf belegten Wert) ·
post_purchase-2 +10 → +14 · post_purchase-3 +14 → +18 · post_delivery-crosssell +21 → +24 + Code-Block (`{% coupon_code 'CHECKOUT15' %}`, „4 days“) + A/B **Code vs. Versand-frei** ·
post_delivery-ugc +30 → +33 · winback-4 live. PLAN in `bin/klaviyo.py`: post_purchase `[(0,min,post_purchase),(24,h,post_purchase-next),(4,d,post_purchase-wait)]`, Filter `["Fulfilled Order"]`;
post_delivery `[(3,d,transit),(4,d,arriving),(4,d,arrived),(3,d,post_purchase-2),(4,d,post_purchase-3),(6,d,crosssell),(3,d,code2),(6,d,ugc),(12,d,vip),(15,d,newin)]`, Filter `["Placed Order","Cancelled Order","Refunded Order"]`.

**Kommandos, in dieser Reihenfolge:** (1) Skript-Erweiterungen 1–4 in `bin/klaviyo.py` (Erweiterung 5 Segment/Sunset separat, nicht blockierend) → `klaviyo.py plan` muss ohne
KeyError durchlaufen · (2) Texte in `state/flows-postpurchase-lang.json` (Autor-Panel + Richter, je Mail A–F wie Welle 1) → `SPECS` um die Datei ergänzen ·
(3) `.venv/bin/python bin/flows.py build --klaviyo --no-proof --nosend state/flows-postpurchase-lang.json` (+ die geänderten Specs), jedes HTML ansehen ·
(4) `bin/klaviyo.py recreate --flows post_purchase,post_delivery` · (5) `bin/klaviyo.py live post_purchase` / `live post_delivery` / `live winback` · (6) `bin/coupons.py plan` (Pool NL15 muss täglich laufen — Plist installiert?) ·
(7) `abstatus` nach 7 Tagen, Beleg `marketing/workflows/04-output/2026-MM-TT-flows-lang.md`.

**Was sein „ja“ braucht:** (a) Rabatt-Weg PD6/7 — 1a Pool NL15 (15 %, 96 h, kein neuer Wert; Klaviyo-Coupon CHECKOUT15 wird nur intern so genannt) · 1b neuer Code mit Name+Wert von ihm ·
1c kein Code, Versand-frei-Pool SHIP (48 h) — **Werte werden nie von uns gesetzt** (rules §Rabattcodes). (b) Abrechnungsname: Scope `read_shopify_payments_accounts` freigeben oder den Text aus
Shopify → Settings → Payments nennen; bis dahin `[DESCRIPTOR]`-Platzhalter, Mails PP1/PP2/PD1 gehen nicht live mit Platzhalter. (c) Live-Schaltung: rules 16.09. „für Klaviyo keine
Rückfragen — bauen, live, melden“ gilt; nur die Code-Mails (PD6/7) warten auf (a).

## 7. Quellen (Web, mit Datum) — keine erfundenen Zahlen, Vendor-Zahlen als solche markiert
- Shopify Enterprise Blog „Shopify Chargeback: 9 Ways to Prevent Disputes“, 08.08.2025 — Descriptor 58 %/27 %, Tracking-Updates, Rückgabe vor Chargeback bei Verspätung, Support sichtbar.
- Shopify Help Center „Chargebacks and inquiries“ (abgerufen 19.09.2026) — Gebühr bei Gewinn regional rückerstattet; $15 USD Shopify Payments US: chargeflow.io / chargebacks911.com (2026).
- ClearlyPayments „Chargeback Dispute Statistics“, 12.06.2024 — 26 % unrecognized, 24 % Produkt, 5–10 % Billing, $2,40 je $1 (eigene Erhebung, unbelegt).
- chargeflow.io „Return Reasons That Predict Chargebacks“ (2026) — „item not received“ 32 % der Friendly-Fraud-Fälle.
- Ravelin „New VAMP for 2025“, 03.06.2025, aktualisiert 01/2026 — 0,5 %/0,7 % Acquirer, 2,2 % → 1,5 % Händler ab 04/2026; Formel (TC40 + TC15)/Sales. chargebacks911 — Mastercard ECP 1,5 % + 100.
- BS&Co „Repeat Purchase Rate Benchmarks: 18.8 % across 156K customers“; Foundry CRO „DTC Fashion Marketing Benchmarks 2026“ 15–17 % (beide Vendor).
- Intern: funnel.md §2 (Post-Purchase: Mail 1 verkauft nichts, Review nach Zustellung), email-cro.md §2 (Review 7–10 d nach Zustellung; Uhrzeiten), psychologie.md §5 (Passform 64 %, Rückgabe sichtbar), api-research.md Z. 55/96/121 (Segment-Trigger, timeframe-Operatoren, Shopify-Metriken inkl. Delivered Shipment).
