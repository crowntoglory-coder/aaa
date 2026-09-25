#!/usr/bin/env python3
"""Klaviyo: unsere Flow-Mails als Templates + Flows anlegen. Fakten: marketing/workflows/01-briefs/2026-09-13-klaviyo/api-research.md

    .venv/bin/python bin/klaviyo.py check                              Key, Scopes, Metriken, Listen
    .venv/bin/python bin/klaviyo.py plan  [--flows a,b]                Trockenlauf ohne Key -> state/klaviyo/plan.json (Baum eingerückt, Splits als [SPLIT])
    .venv/bin/python bin/klaviyo.py apply [--flows a,b] [--list-id X]  Templates + Flows anlegen; Mails bleiben 'draft'
                                                                       (laedt 04-output wie gebaut — vorher flows.py build, wenn Specs neu)
    .venv/bin/python bin/klaviyo.py live FLOW                          Flow-Status auf 'live' — nur auf Ansage
    .venv/bin/python bin/klaviyo.py recreate [--flows a,b] [--draft] [--list-id X]   Flow neu anlegen (alter → Draft + gelöscht), live wie zuvor — nötig nach jeder Textänderung,
                                                                       weil Klaviyo Templates in den Flow klont und Definitionen per API nicht ändert.
                                                                       --draft (sein Wort 20.09.: „mache als entwurf in klaviyo, wenn ich go sage kannst du live
                                                                       schalten“, marketing/…/2026-09-20-flows-verhalten.md §6a/3): alter Flow bleibt live/unberührt,
                                                                       neuer bleibt draft, nichts gelöscht — ids.json merkt die neue ID unter "pending".
    .venv/bin/python bin/klaviyo.py go [--flows a,b]                   Sein "go": pending-Flow (aus recreate --draft) live, alter Flow draft + gelöscht.
    .venv/bin/python bin/klaviyo.py abreport                           A/B-Status je Flow: Gewichte, Betreffs, Empfänger/Klicks/Umsatz wenn der Report-Endpunkt
                                                                       es hergibt (nur GET/Report, nichts geschrieben) -> state/klaviyo/ab-raw.json (Rohantwort)
    .venv/bin/python bin/klaviyo.py abloop --dry                       Nur Liste: welche A/B-Tests fällig für einen Herausforderer sind (concluded + >=200
                                                                       Empfänger/Variante) — baut/schaltet nichts live, nur lesen + Vorschlag
    .venv/bin/python bin/klaviyo.py --selftest                         Ohne Netz: Split-Baum-Fixture (2 Pfade, gleicher Mail-Key) durch flow() bauen, prüfen

Flow-Plan aus _reference/funnel.md §2 + marketing/workflows/02-specs/2026-09-20-flows-verhalten.md (Verhalten statt Wellen: conditional-split je
Zustand, additional_filters je Mail). IDs in state/klaviyo/ids.json (idempotent: Template wird per PATCH erneuert, ein Flow, der schon eine ID hat,
wird nicht doppelt angelegt — Definition aendern geht nur im UI). PLAN-Schritte sind entweder (Wert, Einheit, Mail-Key[, until]) oder
("split", NAME, [Bedingungen], [Schritte JA], [Schritte NEIN]) — rekursiv, ein Split ist immer das letzte Element seiner Liste (Pfade rejoinen nie).
"""
import json, pathlib, re, socket, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "marketing/workflows/04-output/flows"
ST = ROOT / "state/klaviyo"; IDS = ST / "ids.json"
SPECS = ["state/flows-browse.json", "state/flows-v2.json", "state/flows-seq.json", "state/flows-checkout4.json", "state/flows-cart4.json", "state/flows-post2.json", "state/flows-welcome45.json", "state/flows-winback4-sunset.json", "state/flows-postpurchase-lang.json", "state/flows-30tage.json", "state/flows-verhalten.json"]   # alte Cart/Checkout-Specs: state/flows-checkout-old.json (Archiv)
API, REV, FROM = "https://a.klaviyo.com", "2026-07-15", "support@nora-lanelle.com"   # 15.09.: support@ ist die Adresse der Seite (MX hostedemail), hello@ unbelegt
METRICS = ["Viewed Product", "Added to Cart", "Checkout Started", "Placed Order", "Fulfilled Order", "Cancelled Order", "Refunded Order", "Delivered Shipment",
           "Received Email", "Clicked Email"]   # 20.09.: additional_filters je Mail (Kappe + Absichts-Filter) — flows-verhalten.md §6a(1)
NAME = {"welcome": "Welcome", "browse": "Browse Abandonment", "checkout": "Abandoned Checkout (4)", "cart": "Abandoned Cart (4)",
        "post_purchase": "Post-Purchase", "post_delivery": "Post-Delivery (wear + fit note)", "winback": "Winback"}
# Klaviyo-Tags (Help 115005254068): {% unsubscribe %} = fertiger Link, {% unsubscribe_link %} = nur die URL (gehoert in ein href).
ADDR = "Nora Lanelle · Northbound Systems LLC · 5830 E 2nd St, Ste 7000, Casper, WY 82609, USA"   # CAN-SPAM: Postadresse
LINK = '<a href="{% unsubscribe_link %}" style="color:#6b6560">Unsubscribe</a>'
UNSUB = f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;line-height:1.9;color:#6b6560;padding:0 24px 30px">{ADDR}<br>{{% unsubscribe %}}</p>'
# Je Flow: (Trigger-Art, Trigger-Name), Schritte (Wartezeit, Einheit, Mail-Key[, until "HH:MM"]), Filter (Metrik-Name = „= 0 seit Flow-Start“
# oder Tupel (Metrik, Operator, Wert, timeframe_filter), UND), Wiedereintritt. alltime/1 = nie wieder, alltime/0 = jede Bestellung.
# Wartezeit 0 = Mail ist der Einstieg, kein Delay-Knoten. until = delay_until_time in der Ortszeit der Kundin (Spec 19.09. §2: Tages-Delays 07:00).
UNTIL = "07:00"   # Format "HH:MM" — gegen die OpenAPI nicht belegt (Fetch 19.09. abgeschnitten); lehnt Klaviyo den Flow ab, "07:00:00" probieren
PLAN = {
    # 20.09. Spec flows-verhalten.md §3/§6a: Verhalten statt Welle — S1 direkt nach welcome (Käuferin ueberspringt Marke/Beweis/Wahl),
    # S2 Tag 7 nach Klick (warm = alle 8 Mails, kalt spart welcome-3/-5). Ersetzt die flache Kette der 30-tage-Spec (Mails/Delays gleich, nur verzweigt).
    # 20.09. Richter Welle 2: S1 VOR Mail 1 (wie S6 in winback) — welcome-1-kundin (kein WELCOME15, „you already own a piece“) darf nur Kundinnen
    # erreichen; als A/B-Variante von welcome ginge sie zufällig an Neue (unwahr). Neue bekommen welcome (WELCOME15) wie bisher.
    "welcome": (("list", None), [
        ("split", "kundin", [("Placed Order", "greater-than-or-equal", 1, {"type": "date", "operator": "alltime"})],
          [(0, "minutes", "welcome-1-kundin"), (1, "days", "welcome-1b", UNTIL), (7, "days", "welcome-7", UNTIL)],
          [(0, "minutes", "welcome"), (1, "days", "welcome-1b", UNTIL), (2, "days", "welcome-2", UNTIL), (2, "days", "welcome-6", UNTIL),
            ("split", "warm", [("Clicked Email", "greater-than-or-equal", 1, {"type": "date", "operator": "flow-start"})],
              [(2, "days", "welcome-3", UNTIL), (3, "days", "welcome-4", UNTIL), (4, "days", "welcome-5", UNTIL), (7, "days", "welcome-7", UNTIL)],
              [(5, "days", "welcome-4", UNTIL), (4, "days", "welcome-7", UNTIL)])])
        ], ["Placed Order"], {"duration": 1, "unit": "alltime"}),   # Käuferin bekommt keine Welcome 2/3 mehr (Frequenz)
    # Flow-Plan-Prüfung 15.09.: Checkout Started als Filter in browse/cart (sonst laufen cart und checkout parallel), Checkout ≥ 1 h 15 (Klaviyo-Puffer)
    # 20.09. Spec §3 S3: Käuferin (alltime) bekommt browse-1-kundin (kein WELCOME15) statt des harten LAST14-Filters; feuert erst mit Onsite-Tracking (bin/go.sh)
    "browse": (("metric", "Viewed Product"), [
        ("split", "kundin", [("Placed Order", "greater-than-or-equal", 1, {"type": "date", "operator": "alltime"})],
          [(1, "hours", "browse-1-kundin")],
          [(1, "hours", "browse"), (24, "hours", "browse-2"), (48, "hours", "browse-3")])
        ], ["Placed Order", "Added to Cart", "Checkout Started"], {"duration": 7, "unit": "day"}),   # Cart/Checkout bewusst ohne Käuferin-Split (echte Zweitkauf-Absicht, Code passt)
    "cart": (("metric", "Added to Cart"), [(1, "hours", "ca4-1"), (24, "hours", "ca4-2"), (24, "hours", "ca4-3"), (24, "hours", "ca4-4")], ["Placed Order", "Checkout Started"], {"duration": 7, "unit": "day"}),   # 4 Mails (15.09.), Coupons nötig
    # 15.09.: 4 Mails (seine Ansage): easy return → Claire + Code → Code groß 48 h → 24 h + Versand. Codes = Klaviyo-Coupons CHECKOUT15 (96 h) / SHIP24 (24 h),
    # die er in Klaviyo → Coupons anlegt (Shopify-Coupon, Ablauf relativ zur Vergabe) — vorher bleibt der alte 2-Mail-Flow live.
    "checkout": (("metric", "Checkout Started"), [(75, "minutes", "co4-1"), (24, "hours", "co4-2"), (24, "hours", "co4-3"), (24, "hours", "co4-4")], ["Placed Order"], {"duration": 7, "unit": "day"}),
    # 19.09. Spec flows-lang-synchron §2a: PP2 „was jetzt passiert“ +24 h, PP3 „noch nicht verschickt“ Tag 5; Filter Fulfilled Order = 0 seit Start → Kette endet still, sobald verschickt
    "post_purchase": (("metric", "Placed Order"), [(0, "minutes", "post_purchase"), (24, "hours", "post_purchase-next", UNTIL), (4, "days", "post_purchase-wait", UNTIL)], ["Fulfilled Order"], {"duration": 0, "unit": "alltime"}),
    # Zustellung ≈ Tag 10 nach Versand: „so traegst du es“ Tag 10, Passform-Bitte Tag 14 (email-cro.md §2: Review 7–10 Tage nach Zustellung)
    # 17.09.: Rückkauf-Kette Tag 21 Cross-Sell, Tag 30 Foto (UGC), Tag 45 VIP (seine Ansage „Flows bis 30 Mails“; Spec state/flows-post2.json)
    # 15.09.: Transit-Mail Tag 3 nach Versand (Erwartung, Tracking, Kontakt, Rückgabe statt Rückbuchung — seine Ziele Rückkauf/Chargeback/Zufriedenheit)
    # 19.09. Spec §2b (kumuliert ab Versand): Transit 3 · Arriving 7 · Arrived 11 · Wear 14 · Fit 18 · Cross-Sell+Code 24 · Code endet 27 · UGC 33 · VIP 45 · New In 60;
    # Filter: neue Bestellung / Storno / Erstattung seit Start stoppt die Kette (neue Bestellung startet sie neu: reentry alltime/0)
    # 20.09. Spec §6a Beispiel wörtlich: S4 nach "arrived" — Käuferin 2+ bekommt den VIP-Pfad statt Rabatt-Ketten (kein eigener VIP-Flow mehr),
    # Käuferin 1 bekommt S5 (Klick Tag 33) warm/kalt. vip-1..3 sind neue Mail-Keys — flows.py build muss sie zuerst nach 04-output legen.
    "post_delivery": (("metric", "Fulfilled Order"),
      [(3, "days", "post_purchase-transit", UNTIL), (4, "days", "post_delivery-arriving", UNTIL), (4, "days", "post_delivery-arrived", UNTIL),
       ("split", "wieder", [("Placed Order", "greater-than-or-equal", 2, {"type": "date", "operator": "alltime"})],
         [(7, "days", "post_purchase-3", UNTIL), (2, "days", "vip-1", UNTIL), (8, "days", "vip-2", UNTIL), (17, "days", "vip-3", UNTIL), (15, "days", "post_delivery-newin", UNTIL)],
         [(3, "days", "post_purchase-2", UNTIL), (4, "days", "post_purchase-3", UNTIL), (6, "days", "post_delivery-crosssell", UNTIL), (3, "days", "post_delivery-code2", UNTIL),
          ("split", "warm", [("Clicked Email", "greater-than-or-equal", 1, {"type": "date", "operator": "flow-start"})],
            [(6, "days", "post_delivery-ugc", UNTIL), (5, "days", "post_delivery-style", UNTIL), (7, "days", "post_delivery-vip", UNTIL), (7, "days", "post_delivery-season", UNTIL), (8, "days", "post_delivery-newin", UNTIL)],
            [(18, "days", "post_delivery-vip", UNTIL), (15, "days", "post_delivery-newin", UNTIL)])])],
      ["Placed Order", "Cancelled Order", "Refunded Order"], {"duration": 0, "unit": "alltime"}),
    # 20.09. Spec §3 winback: S6 am Eintritt (vor der ersten Mail) — Käuferin 2+ "wieder" nie ein Rabatt-Code (Marge, Quellen 5/11), "erst" S7 Tag 150 Klick warm/kalt.
    "winback": (("metric", "Placed Order"), [
        ("split", "wieder", [("Placed Order", "greater-than-or-equal", 2, {"type": "date", "operator": "alltime"})],
          [(90, "days", "winback", UNTIL), (7, "days", "winback-2", UNTIL), (21, "days", "winback-5", UNTIL)],
          [(90, "days", "winback", UNTIL), (7, "days", "winback-2", UNTIL), (7, "days", "winback-3", UNTIL), (14, "days", "winback-4", UNTIL),
            ("split", "warm", [("Clicked Email", "greater-than-or-equal", 1, {"type": "date", "operator": "flow-start"})],
              [(32, "days", "winback-5", UNTIL)], [])])
        ], ["Placed Order"], {"duration": 0, "unit": "alltime"}),   # je Bestellung neu (Rückkauf-Ziel), Filter verhindert Doppel
    # TODO sunset (Erweiterung 5, Spec 19.09. §4): braucht Segment-Trigger {"type":"segment","id":…} (Opened/Clicked/Placed Order = 0 in 90 Tagen, Profil > 90 Tage, ≥3 Mails),
    # dazu `klaviyo.py segment NAME` (POST /api/segments, auch „PP 0–14“ als Kampagnen-Ausschluss) und im Flow 14 d Wartezeit + conditional-split + Suppression —
    # PLAN kann nur Delay→Mail-Ketten; Segment-Definition-Schema ungeprüft. Spec-Mail "sunset" liegt in state/flows-winback4-sunset.json, baut per flows.py; Flow im UI anlegen.
}
M = {m["flow"]: m for s in SPECS for m in json.loads((ROOT / s).read_text())}   # Mail-Key -> Spec (welcome, welcome-2, ...)
NO_SMART = ("post_purchase", "post_purchase-transit", "post_purchase-wait", "post_delivery-arriving", "post_delivery-arrived", "cart", "checkout", "co4-1", "ca4-1")   # Service-Mails Tag 1/5/7/11 nie überspringen (Smart Sending skippt, verschiebt nicht); Spec-Feld "smart_sending" gewinnt
CAP = [("Received Email", "less-than-or-equal", 2, {"type": "date", "operator": "in-the-last", "quantity": 7, "unit": "day"})]   # 20.09. Default-Frequenzkappe je Mail, flows-verhalten.md §4


SOFT = False   # True waehrend plan(): fehlende Mail-Keys (vip-1..3, winback-5, sunset-2 — PLAN kennt sie schon, Text kommt erst durch flows.py build) werden als Platzhalter angezeigt statt abzubrechen


def mspec(k):
    """M[k], mit klarer Fehlermeldung statt KeyError — PLAN darf Keys nennen, die state/flows-*.json noch nicht kennt.
    Im SOFT-Modus (nur plan(), kein Netz-Schreibzugriff) ein Platzhalter-Spec statt Abbruch, damit der Baum trotzdem
    sichtbar wird; apply()/recreate() bleiben hart — ohne echten Text kein Schreibzugriff."""
    m = M.get(k)
    if m: return m
    if SOFT: return {"flow": k, "subject": f"[Platzhalter] {k}", "preview": "Text fehlt — flows.py build", "smart_sending": True}
    sys.exit(f"Mail-Key '{k}' fehlt in den Specs (state/flows-*.json) — erst flows.py build, dann apply/recreate")


def _walk(nodes):
    """Alle Mail-Schritte eines PLAN-Astes, Splits rekursiv in beide Pfade aufgeloest, als 4-Tupel (Wert, Einheit, Mail-Key, until|None).
    Ein Mail-Key aus zwei Pfaden erscheint zweimal — fuer Template-Sammlung reicht das (dieselbe Vorlage, siehe flow())."""
    for node in nodes:
        if node[0] == "split": yield from _walk(node[3]); yield from _walk(node[4])
        else: yield tuple(node) + (None,) * (4 - len(node))


def steps(f):
    """Schritte als 4-Tupel (Wert, Einheit, Mail-Key, until|None); Splits aufgeloest (beide Pfade)."""
    return list(_walk(PLAN[f][1]))


def mail_filters(k, mids):
    """additional_filters je Mail (Erweiterung 20.09., flows-verhalten.md §6a(1)): Default-Kappe (Received Email <= 2/7d)
    fuer alle Keys ausser NO_SMART, plus optionales Spec-Feld "filters" je Mail (state/flows-*.json) in derselben Form
    wie filters(). Jede Bedingung eine eigene Gruppe (UND) — ODER innerhalb einer Bedingung ist hier nicht gebaut
    (kein Flow im PLAN braucht es heute); ponytail: bei Bedarf (z.B. ca4-3 "Klick ODER Viewed Product") eine Liste von
    Tupeln je Gruppe zulassen statt eines Tupels je Gruppe."""
    m = M.get(k, {})
    conds = (list(CAP) if k not in NO_SMART else []) + [(x, "equals", 0, {"type": "date", "operator": "flow-start"}) if isinstance(x, str) else tuple(x) for x in m.get("filters", [])]
    conds = [c for c in conds if c[0] in mids]
    if not conds: return None
    return {"condition_groups": [{"conditions": [{"type": "profile-metric", "metric_id": mids[n], "measurement": "count",
            "measurement_filter": {"type": "numeric", "operator": op, "value": val}, "timeframe_filter": tf}]} for n, op, val, tf in conds]}


def filters(f):
    """Filter als 4-Tupel (Metrik, Operator, Wert, timeframe_filter); nackter Name = „= 0 seit Flow-Start“."""
    return [(x, "equals", 0, {"type": "date", "operator": "flow-start"}) if isinstance(x, str) else x for x in PLAN[f][2]]


def key():
    """Gleiche Lesart wie bin/shopify_edit.py env(); der Wert wird nirgends ausgegeben."""
    # 15.09.: der Guard laesst die Sitzung nicht an .env; bis er die Zeile selbst uebernimmt, liegt der Key in state/klaviyo.key (chmod 600, *.key ist gitignored)
    txt = "\n".join(p.read_text() for p in (ROOT / ".env", ROOT / "state/klaviyo.key") if p.is_file())
    return dict(re.findall(r"^([A-Z0-9_]+)=(.*)$", txt, re.M)).get("KLAVIYO_PRIVATE_KEY", "").strip()


RETRY_DELAYS = (5, 15, 45)  # Sekunden — Nacht-Stabilitaet: DNS/Netz kurz weg, nicht sofort aufgeben


def _urlopen(req, timeout):
    """urllib.request.urlopen mit 3 Versuchen bei reinen Netzfehlern (kein HTTP-Fehler — der ist
    eine Antwort vom Server, kein Ausfall, deshalb sofort weiterreichen)."""
    for i, delay in enumerate(RETRY_DELAYS):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, ConnectionResetError, socket.timeout):
            if i == len(RETRY_DELAYS) - 1:
                raise
            time.sleep(delay)


def api(method, path, body=None, timeout=60, soft=False):
    """Ein Request, JSON rein/raus. 429 -> Retry-After abwarten; nach jedem Call 1,2 s Pause (Create Flow: Burst 1/s).
    soft=True: ein HTTP-Fehler beendet den Prozess nicht, sondern kommt als {"error": "..."} zurueck (fuer Report-Aufrufe,
    die je nach Metrik/Konto ablehnen koennen — der Aufrufer soll das abfangen, nicht das ganze Skript abbrechen)."""
    k = key() or sys.exit("KLAVIYO_PRIVATE_KEY fehlt in .env")
    url = path if path.startswith("http") else API + path
    hdr = {"Authorization": f"Klaviyo-API-Key {k}", "revision": REV, "Accept": "application/vnd.api+json", "Content-Type": "application/vnd.api+json"}
    for _ in range(4):
        req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, method=method, headers=hdr)
        try:
            with _urlopen(req, timeout) as r:
                raw = r.read(); time.sleep(1.2)
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                w = int(e.headers.get("Retry-After", "10"))   # Create Flow: 100/Tag -> Retry-After in Stunden; nicht stumm warten
                if w > 120: sys.exit(f"{method} {path} -> 429, Retry-After {w}s — spaeter erneut, ids.json haelt den Stand")
                time.sleep(w + 1); continue
            if soft: return {"error": f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"}
            sys.exit(f"{method} {path} -> HTTP {e.code}: {e.read().decode(errors='replace')[:600]}")   # Fehlertext ohne Key
    if soft: return {"error": "dauerhaft 429"}
    sys.exit(f"{method} {path}: dauerhaft 429")


def pages(path):
    """Cursor-Paging: links.next ist eine volle URL."""
    while path:
        r = api("GET", path); yield from r.get("data", []); path = (r.get("links") or {}).get("next")


def metrics():
    """Name -> ID. Bei Doppelgaengern (API-Events gleichen Namens) gewinnt die Shopify-Integration (Help 115005080447)."""
    out = {}
    for d in pages("/api/metrics"):
        n, integ = d["attributes"]["name"], ((d["attributes"].get("integration") or {}).get("name") or "")
        if n not in out or integ == "Shopify": out[n] = d["id"]
    return out


def list_id(override=None):
    """--list-id gewinnt; sonst „Email List“ (dorthin schreibt die Shopify-Integration das Popup), sonst 'newsletter' im Namen.
    Nie still die erste: 24.09. war das „Preview List“ → Welcome hörte ins Leere, 0 Mails seit Start (traps.md)."""
    if override: return override
    ls = list(pages("/api/lists")) or sys.exit("keine Liste im Konto — --list-id angeben")
    hit = [l for l in ls if l["attributes"]["name"].lower() == "email list"] or [l for l in ls if "newsletter" in l["attributes"]["name"].lower()]
    return hit[0]["id"] if hit else sys.exit("keine 'Email List'/'newsletter'-Liste (" + ", ".join(f"{l['attributes']['name']}={l['id']}" for l in ls) + ") — --list-id angeben")


def template(m, label=None):
    """CODE-Template aus dem gebauten HTML (04-output, wie geprueft). Shopify-Tag im href -> Klaviyo-URL-Tag; ein nackter
    {% unsubscribe_link %} aus einem --klaviyo-Build stuende als blanke URL im Fuss -> wieder ein Link.
    Textmails: plain()-Wrapper aus flows.py hat keinen Fuss -> Adresse + Abmeldelink anhaengen, dazu 'text'."""
    key = m["flow"] + (f"~{label}" if label else "")
    p = OUT / f"{key}.html"
    if not p.is_file():
        if SOFT: return {"data": {"type": "template", "attributes": {"name": "NL " + key, "editor_type": "CODE", "html": "<!-- Platzhalter: flows.py build -->"}}}
        sys.exit(f"04-output fehlt: {p} — erst flows.py build")
    h = p.read_text().replace("{{ unsubscribe_url }}", "{% unsubscribe_link %}")
    h = re.sub(r'(?<!href=")\{% unsubscribe_link %\}', LINK, h)
    attrs = {"name": "NL " + key, "editor_type": "CODE", "html": h}
    if m.get("type") == "text":
        v = next((x for x in m.get("ab", []) if x["label"] == label), None) if label else None
        text = m["text"]
        if v and v.get("text_open"): parts = text.split("\n\n"); parts[1] = v["text_open"]; text = "\n\n".join(parts)
        attrs["html"] = h.replace("</body>", UNSUB + "</body>")
        attrs["text"] = f"{text}\n\n{ADDR}\nUnsubscribe: {{% unsubscribe_link %}}"
    return {"data": {"type": "template", "attributes": attrs}}


def flow(f, tids, mids, lid):
    """Kette [delay ->] mail [-> delay -> mail ...], kann sich mit einem conditional-split verzweigen (PLAN-Schrittform
    ("split", NAME, [Bedingungen], [Schritte JA], [Schritte NEIN]), rekursiv — Spec flows-verhalten.md §6a(2); ein Split
    ist immer das letzte Element seiner Liste, Pfade rejoinen nie. Flow-Filter-Gruppen sind UND (Spec: Gruppen AND,
    innerhalb OR). Mails mit `ab` (16.09.) werden als ab-test-Action angelegt: A = Basis, B/C = andere Einstiege,
    Gewinner nach Klicks automatisch. additional_filters je Mail: mail_filters() (Kappe + optionales Spec-Feld "filters")."""
    (ttype, tname), _, _, reentry = PLAN[f]
    trig = {"type": "list", "id": lid} if ttype == "list" else {"type": "metric", "id": mids[tname], "trigger_filter": None}
    filt = [x for x in filters(f) if x[0] in mids]   # Erweiterung 2: fehlende Filter-Metrik → nur den Filter weglassen, nicht den Flow
    for x in filters(f):
        if x[0] not in mids: print(f"! {f}: Filter-Metrik fehlt: {x[0]} — Filter weggelassen")

    def send(tmp, k, i, label=None, branch=""):
        m = mspec(k); founder = m.get("type") == "text"
        v = next((x for x in m.get("ab", []) if x["label"] == label), {}) if label else {}
        name = f"{NAME[f]} #{i + 1}" + (f" {branch}" if branch else "") + (f" {label}" if label else "")
        return {"temporary_id": tmp, "type": "send-email", "links": {"next": None}, "data": {"status": "draft", "message": {
            "name": name, "from_email": FROM, "from_label": "Claire, Nora Lanelle" if founder else "Nora Lanelle",
            "reply_to_email": FROM, "cc_email": None, "bcc_email": None, "subject_line": v.get("subject") or m["subject"], "preview_text": v.get("preview") or m.get("preview", ""),
            "template_id": tids.get(f"NL {k}" + (f"~{label}" if label else ""), f"<template:NL {k}>"), "smart_sending_enabled": bool(m.get("smart_sending", k not in NO_SMART)),
            "transactional": False, "add_tracking_params": True, "custom_tracking_params": None, "additional_filters": mail_filters(k, mids)}}}

    def build(nodes, tag, branch):
        """Eine Ebene: Mail-Schritte, optional mit einem terminalen Split. Gibt (acts, first_temporary_id) zurueck;
        `tag` macht temporary_ids ueber Pfade eindeutig (gleicher Mail-Key in zwei Zweigen -> eigene send-Action, Pre-Mortem #5)."""
        acts, chain = [], []
        for i, node in enumerate(nodes):
            if node[0] == "split":
                if i != len(nodes) - 1: sys.exit(f"{f}: Split '{node[1]}' ist nicht das letzte Element seiner Liste (Splits sind terminal)")
                _, sname, conds, tsteps, fsteps = node
                sid = f"sp_{tag}_{sname}"
                tacts, tfirst = build(tsteps, f"{tag}{sname}t", sname)
                facts, ffirst = build(fsteps, f"{tag}{sname}f", f"nicht-{sname}")
                cg = [{"conditions": [{"type": "profile-metric", "metric_id": mids[cn], "measurement": "count",
                      "measurement_filter": {"type": "numeric", "operator": op, "value": val}, "timeframe_filter": tf}]} for cn, op, val, tf in conds if cn in mids]
                acts.append({"temporary_id": sid, "type": "conditional-split", "links": {"next_if_true": tfirst, "next_if_false": ffirst},
                             "data": {"profile_filter": {"condition_groups": cg}}})
                chain.append(sid); acts += tacts + facts
            else:
                v, unit, k, until = tuple(node) + (None,) * (4 - len(node))
                if until and unit == "hours" and v % 24 == 0: v, unit = v // 24, "days"   # 24.09.: Klaviyo 400 — delay_until_time nur bei 'days'
                if unit != "days": until = None
                m = mspec(k); base = f"{tag}{i}"
                if v:
                    did = f"d{base}"
                    acts.append({"temporary_id": did, "type": "time-delay", "links": {"next": None},
                                 "data": {"unit": unit, "value": v, "secondary_value": 0, "timezone": "profile", "delay_until_time": until, "delay_until_weekdays": None}})
                    chain.append(did)
                mid_ = f"m{base}"
                if m.get("ab"):
                    variations = [send(f"{mid_}a", k, i, branch=branch)] + [send(f"{mid_}{x['label'].lower()}", k, i, x["label"], branch) for x in m["ab"]]
                    acts.append({"temporary_id": mid_, "type": "ab-test", "links": {"next": None}, "data": {"main_action": send(f"{mid_}m", k, i, branch=branch),
                                 "current_experiment": {"name": f"{NAME[f]} #{i + 1}" + (f" {branch}" if branch else "") + ": Einstieg", "variations": variations, "winner_metric": "unique-clicks",
                                                        "automatic_winner_selection_settings": {"enabled": True, "automatic_end_date": None, "automatic_end_statistical_certainty": True}}}})
                else:
                    acts.append(send(mid_, k, i, branch=branch))
                chain.append(mid_)
        for a, b in zip(chain, chain[1:]):
            act = next(x for x in acts if x["temporary_id"] == a)
            if act["type"] != "conditional-split": act["links"]["next"] = b
        return acts, (chain[0] if chain else None)

    acts, first = build(PLAN[f][1], "", "")
    pf = {"condition_groups": [{"conditions": [{"type": "profile-metric", "metric_id": mids[n], "measurement": "count",
          "measurement_filter": {"type": "numeric", "operator": op, "value": val}, "timeframe_filter": tf}]} for n, op, val, tf in filt]} if filt else None
    return {"data": {"type": "flow", "attributes": {"name": NAME[f], "definition": {
        "triggers": [trig], "profile_filter": pf, "entry_action_id": first, "reentry_criteria": reentry, "actions": acts}}}}


def _cond_str(conds):
    return " & ".join(f"{n}{'=' if op == 'equals' else ' ' + op + ' '}{val}" for n, op, val, tf in conds)


def _print_nodes(nodes, tmpls, prefix):
    """Baum eingerückt (20.09., Spec §6a: "summary()/plan.json zeigen den Baum eingerückt")."""
    for node in nodes:
        if node[0] == "split":
            _, name, conds, tsteps, fsteps = node
            print(f"{prefix}[SPLIT {name}] {_cond_str(conds)}")
            print(f"{prefix}  JA:"); _print_nodes(tsteps, tmpls, prefix + "    ")
            print(f"{prefix}  NEIN:"); _print_nodes(fsteps, tmpls, prefix + "    ")
        else:
            v, u, k, until = tuple(node) + (None,) * (4 - len(node))
            m = mspec(k)
            kb = len(tmpls[f"NL {k}"]["data"]["attributes"]["html"].encode()) / 1024
            ss = "" if m.get("smart_sending", k not in NO_SMART) else " smart-off"
            print(f"{prefix}+{v:>3} {u[0]}{(' @' + until) if until else '     '} {k:22} {kb:5.1f} KB  {'text' if m.get('type') == 'text' else 'html'}{ss}  \"{m['subject']}\"")


def summary(f, tmpls):
    (tt, tn), _, _, re_ = PLAN[f]
    fs = " & ".join(f"{n}{'=' if op == 'equals' else ' ' + op + ' '}{val}" + ("" if tf.get("operator") == "flow-start" else f" ({tf.get('operator')} {tf.get('quantity', '')} {tf.get('unit', '')})") for n, op, val, tf in filters(f))
    print(f"{f}: trigger {tt} {tn or 'Newsletter'} | filter {fs or '-'} | reentry {re_['unit']}/{re_['duration']}")
    _print_nodes(PLAN[f][1], tmpls, "   ")


def check():
    ls, mids = list(pages("/api/lists")), metrics()
    print("Listen:", ", ".join(f"{l['attributes']['name']} ({l['id']})" for l in ls) or "keine")
    for n in METRICS: print(f"  {'ok' if n in mids else '--'} {n:17} {mids.get(n, 'fehlt — Viewed Product/Added to Cart brauchen das Onsite-Snippet')}")


def plan(only):
    """Nie ein Schreib-Endpunkt; Platzhalter-IDs, damit es ohne Key laeuft. Liest die zuletzt gebauten HTMLs (Groessen)."""
    global SOFT; SOFT = True
    mids = {n: f"<metric:{n}>" for n in METRICS}
    tids = {f"NL {k}{s}": f"<template:NL {k}{s}>" for k, m in M.items() for s in [""] + [f"~{x['label']}" for x in m.get("ab", [])]}
    out = {"templates": {}, "flows": {}}
    for f in [f for f in PLAN if not only or f in only]:
        for k in dict.fromkeys(k for _, _, k, _ in steps(f)): out["templates"][f"NL {k}"] = template(mspec(k))
        out["flows"][f] = flow(f, tids, mids, "<list:Newsletter>"); summary(f, out["templates"])
    SOFT = False
    ST.mkdir(parents=True, exist_ok=True); (ST / "plan.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print("-> state/klaviyo/plan.json")


NO_FIND = False


def find(kind, name):
    """Falls ids.json fehlt: gleichnamiges Template/Flow wiederfinden statt ein Duplikat anzulegen (Flows: 100/Tag)."""
    d = api("GET", f"/api/{kind}?filter=" + urllib.parse.quote(f'equals(name,"{name}")')).get("data")
    return d[0]["id"] if d else None


def apply(only, lid_override):
    """Kein Rebuild: hochgeladen wird, was in 04-output liegt und als PNG geprueft wurde (plan liest dieselben Dateien)."""
    ids = json.loads(IDS.read_text()) if IDS.is_file() else {"templates": {}, "flows": {}}
    save = lambda: (ST.mkdir(parents=True, exist_ok=True), IDS.write_text(json.dumps(ids, indent=1)))
    mids, flows = metrics(), []
    for f in [f for f in PLAN if not only or f in only]:
        (tt, tn), _, _, _ = PLAN[f]
        if tt == "metric" and tn not in mids: print(f"! {f}: Trigger-Metrik fehlt: {tn} (Onsite-Snippet? 'check' zeigt, was da ist) — uebersprungen")   # fehlende Filter-Metrik: flow() lässt nur den Filter weg
        else: flows.append(f)
    lid = list_id(lid_override) if "welcome" in flows else None
    for f in flows:
        for k in dict.fromkeys(k for _, _, k, _ in steps(f)):
          for label in [None] + [x["label"] for x in mspec(k).get("ab", [])]:
            name, body = "NL " + k + (f"~{label}" if label else ""), template(mspec(k), label)
            tid = ids["templates"].get(name) or find("templates", name)
            if tid:   # editor_type ist nach dem Anlegen nicht aenderbar, also raus aus dem PATCH
                api("PATCH", f"/api/templates/{tid}", {"data": {"type": "template", "id": tid, "attributes": {a: v for a, v in body["data"]["attributes"].items() if a != "editor_type"}}})
            else:
                tid = api("POST", "/api/templates", body)["data"]["id"]
            ids["templates"][name] = tid; save(); print(f"  template {name} -> {tid}")
        fid = ids["flows"].get(f) or (None if NO_FIND else find("flows", NAME[f]))
        if fid:
            ids["flows"][f] = fid; save(); print(f"  flow {f} existiert: https://www.klaviyo.com/flow/{fid}/edit (Definition nur im UI aendern)"); continue
        fid = api("POST", "/api/flows", flow(f, ids["templates"], mids, lid))["data"]["id"]
        ids["flows"][f] = fid; save(); print(f"  flow {f} -> https://www.klaviyo.com/flow/{fid}/edit")


def sync(only=None):
    """Live-Flows tragen KOPIEN der Templates (Klaviyo klont beim Anlegen) — ein PATCH auf unser Template erreicht sie nicht (15.09., „Returns free“
    stand noch in Welcome #1). Also je Flow-Action das Message-Template mit dem frischen Build überschreiben."""
    ids = json.loads(IDS.read_text()) if IDS.is_file() else {"flows": {}}
    for f, fid in ids["flows"].items():
        if only and f not in only or f not in PLAN: continue
        keys = [k for _, _, k, _ in steps(f)]
        acts = [a for a in pages(f"/api/flows/{fid}/flow-actions") if a["attributes"]["definition"].get("type") == "send-email"]
        acts.sort(key=lambda a: int(a["id"]))
        for i, a in enumerate(acts):
            if i >= len(keys): break
            msg = a["attributes"]["definition"]["data"]["message"]; tid = msg.get("template_id")
            if not tid: continue
            body = template(mspec(keys[i]))["data"]["attributes"]
            api("PATCH", f"/api/templates/{tid}", {"data": {"type": "template", "id": tid, "attributes": {k2: v for k2, v in body.items() if k2 != "editor_type"}}})
            print(f"  sync {f} #{i + 1} {keys[i]:14} -> {tid} ({msg.get('name')})")


def recreate(only=None, lid_override=None, draft=False):
    """Flow-Definitionen sind per API nicht änderbar und Message-Templates sind Klone (PATCH → 404). Also: alten Flow umbenennen + auf Draft,
    neuen Flow mit frischen Templates anlegen, live setzen, wenn der alte live war (15.09.).
    --draft (sein Wort 20.09.: „mache als entwurf in klaviyo, wenn ich go sage kannst du live schalten“, flows-verhalten.md §6a/3):
    alter Flow bleibt live/unberührt, neuer Flow entsteht als Draft daneben; ids.json merkt ihn unter "pending" statt "flows" —
    `go` schaltet ihn live und räumt den alten weg."""
    global NO_FIND
    todo = [f for f in list((json.loads(IDS.read_text()) if IDS.is_file() else {"flows": {}})["flows"]) if (not only or f in only) and f in PLAN]
    for f in todo:
        ids = json.loads(IDS.read_text()); fid = ids["flows"][f]                     # je Runde frisch lesen: apply() schreibt die Datei
        if draft:
            ids["flows"].pop(f); ST.mkdir(parents=True, exist_ok=True); IDS.write_text(json.dumps(ids, indent=1))
            NO_FIND = True
            apply([f], lid_override); NO_FIND = False
            ids = json.loads(IDS.read_text()); new_fid = ids["flows"].pop(f)
            ids.setdefault("pending", {})[f] = new_fid; ids["flows"][f] = fid
            IDS.write_text(json.dumps(ids, indent=1))
            print(f"  {f}: Entwurf {new_fid} (draft) neben live {fid} — https://www.klaviyo.com/flow/{new_fid}/edit ('go' schaltet live)")
            continue
        was = api("GET", f"/api/flows/{fid}")["data"]["attributes"]["status"]
        ids["flows"].pop(f); ST.mkdir(parents=True, exist_ok=True); IDS.write_text(json.dumps(ids, indent=1))
        NO_FIND = True
        try: apply([f], lid_override)
        except SystemExit:   # 24.09.: erst neu bauen, dann alt abschalten — scheitert der Neubau, bleibt der alte Flow unberührt (vorher: post_purchase stand ohne Flow da)
            ids = json.loads(IDS.read_text()); ids["flows"][f] = fid; IDS.write_text(json.dumps(ids, indent=1)); raise
        NO_FIND = False
        if was == "live": live(f)
        api("PATCH", f"/api/flows/{fid}", {"data": {"type": "flow", "id": fid, "attributes": {"status": "draft"}}})   # Name ist per API nicht änderbar
        api("DELETE", f"/api/flows/{fid}"); print(f"  {f}: alt {fid} (war {was}) -> draft + gelöscht")


def go(only=None):
    """Sein 'go' (flows-verhalten.md §6a/3, §3 Bau-Reihenfolge Schritt 5): pending-Flow aus 'recreate --draft' live schalten —
    neuer Flow + A/B-Tests live, alter Flow draft + gelöscht, ids.json 'pending' -> 'flows'."""
    ids = json.loads(IDS.read_text()) if IDS.is_file() else {"flows": {}, "pending": {}}
    todo = [f for f in ids.get("pending", {}) if not only or f in only]
    if not todo: print("keine wartenden Entwuerfe — erst 'recreate --draft'"); return
    for f in todo:
        ids = json.loads(IDS.read_text()); new_fid = ids["pending"].pop(f); old_fid = ids["flows"].get(f)
        e = _set_live(new_fid)
        if old_fid:
            api("PATCH", f"/api/flows/{old_fid}", {"data": {"type": "flow", "id": old_fid, "attributes": {"status": "draft"}}})
            api("DELETE", f"/api/flows/{old_fid}")
        ids["flows"][f] = new_fid
        ST.mkdir(parents=True, exist_ok=True); IDS.write_text(json.dumps(ids, indent=1))
        print(f"{f}: {new_fid} -> live ({e} A/B-Tests), alt {old_fid} draft+gelöscht")


def abstatus():
    """Laufende A/B-Tests je Flow: Start, Gewichte (Klaviyo verschiebt sie automatisch zum Gewinner), Varianten-Betreffs."""
    ids = json.loads(IDS.read_text())
    for f, fid in ids["flows"].items():
        d = api("GET", f"/api/flows/{fid}?additional-fields[flow]=definition")["data"]["attributes"]
        for a in d["definition"]["actions"]:
            if a["type"] != "ab-test": continue
            ex = a["data"]["current_experiment"]; al = ex.get("allocations") or {}
            print(f"{f:14} {d['status']:5} exp={a['data'].get('experiment_status'):5} seit {str(ex.get('started') or '-')[:16]}")
            for v in ex["variations"]:
                print(f"    {al.get(v['id'], 0):.2f}  {v['data']['message']['subject_line']}")


def flow_report(fid, metric_id):
    """Empfaenger/Klicks/Umsatz je Flow-Message ueber den Report-Endpunkt (POST, aber lesend — keine Mutation).
    Feld-Check 19.09.: group_by braucht flow_id + flow_message_id zusammen; unsere Placed-Order-Metrik (Shopify-Event)
    lehnt 'conversion_value' ab ("does not support querying for values data", HTTP 400) — dann ohne Umsatz nochmal,
    Empfaenger/Klicks gehen. Ergebnis (results, hinweis); results bei 0 Bestellungen/Traffic leer, kein Fehler."""
    body = lambda stats: {"data": {"type": "flow-values-report", "attributes": {
        "timeframe": {"key": "last_30_days"}, "conversion_metric_id": metric_id,
        "filter": f'equals(flow_id,"{fid}")', "group_by": ["flow_id", "flow_message_id"], "statistics": stats}}}
    r = api("POST", "/api/flow-values-reports/", body(["recipients", "click_rate", "conversion_value"]), soft=True)
    if "error" not in r: return r["data"]["attributes"]["results"], None
    r2 = api("POST", "/api/flow-values-reports/", body(["recipients", "click_rate"]), soft=True)
    if "error" not in r2: return r2["data"]["attributes"]["results"], "Umsatz im UI (Metrik ohne Werte-Abfrage)"
    return [], r2["error"][:120]


def abreport():
    """Nur Lesen: A/B-Status je laufendem Test (Gewichte, Betreffs, wenn moeglich Empfaenger/Klicks/Umsatz).
    Rohe ab-test-Definitionen + Report-Antwort -> state/klaviyo/ab-raw.json, damit die echten Feldnamen fuer
    winning_metric/auto-conclude/flow_message_id ablesbar sind, sobald Bestellungen da sind (nicht raten).
    flow_report() einmal je Flow (nicht je ab-test-Action): group_by liefert ohnehin alle flow_message_id
    des Flows in einer Antwort — der Report-Endpunkt ist deutlich enger rate-gelimited als der Rest der API,
    mehrfach dieselbe Frage stellen kostet nur Zeit (19.09. an mehreren Checkout-Mails beobachtet)."""
    ids = json.loads(IDS.read_text()) if IDS.is_file() else {"flows": {}}
    po = metrics().get("Placed Order")
    raw, n = {}, 0
    for f, fid in ids["flows"].items():
        d = api("GET", f"/api/flows/{fid}?additional-fields[flow]=definition")["data"]["attributes"]
        acts = [a for a in d["definition"]["actions"] if a["type"] == "ab-test"]
        if not acts: continue
        results, note = flow_report(fid, po) if po else ([], "Placed-Order-Metrik fehlt — 'check' pruefen")
        by_id = {row.get("groupings", {}).get("flow_message_id"): row.get("statistics", {}) for row in results}
        raw[f] = {"report": results, "ab_tests": []}
        for i, act in enumerate(acts):
            n += 1
            ex = act["data"]["current_experiment"]
            raw[f]["ab_tests"].append({"experiment_status": act["data"].get("experiment_status"), "current_experiment": ex})
            since = str(ex.get("started") or "-")[:10]
            print(f"📧 {f} #{i + 1}: {act['data'].get('experiment_status')} seit {since}")
            for v in ex["variations"]:
                label = v["data"]["message"]["name"].rsplit(" ", 1)[-1]
                w = (ex.get("allocations") or {}).get(v["id"], 0)
                st = by_id.get(v["id"]) or by_id.get(v["data"]["message"].get("id")) or {}
                rec, rev = st.get("recipients"), st.get("conversion_value")
                extra = f" · {rec} Empf." + (f" · ${rev:.2f}" if rev is not None else "") if rec is not None else ""
                print(f"   {label} {w:.2f}{extra}  \"{v['data']['message']['subject_line']}\"")
            if note: print(f"   ({note})")
    if not n: print("keine laufenden A/B-Tests")
    ST.mkdir(parents=True, exist_ok=True); (ST / "ab-raw.json").write_text(json.dumps(raw, indent=1, ensure_ascii=False))
    print("-> state/klaviyo/ab-raw.json")


def abloop(dry=True):
    """Nur Liste, nie live()/recreate() — das Bauen eines Herausforderers (Text ueber urteil, flows.py build, klaviyo.py
    recreate) bleibt ein eigener Schritt nach seinem 'ja' (Sichtbarkeit). Faellig = experiment_status concluded/ended UND
    jede Variante >= 200 Empfaenger laut Report; ohne Zahl gilt das als nicht erreicht (nie raten, s. abreport-Hinweis)."""
    ids = json.loads(IDS.read_text()) if IDS.is_file() else {"flows": {}}
    po = metrics().get("Placed Order")
    for f, fid in ids["flows"].items():
        d = api("GET", f"/api/flows/{fid}?additional-fields[flow]=definition")["data"]["attributes"]
        acts = [a for a in d["definition"]["actions"] if a["type"] == "ab-test"]
        report = None   # je Flow hoechstens einmal geladen (Report-Endpunkt eng rate-gelimited), nur wenn ueberhaupt gebraucht
        for i, act in enumerate(acts):
            status = act["data"].get("experiment_status")
            if status not in ("concluded", "ended"):
                print(f"{f} #{i + 1}: laeuft noch ({status}) — naechste Pruefung Sonntag"); continue
            if report is None: report = flow_report(fid, po)[0] if po else []
            recips = [row.get("statistics", {}).get("recipients", 0) for row in report]
            nvar = len(act["data"]["current_experiment"]["variations"])
            if len(recips) < nvar or min(recips or [0]) < 200:
                print(f"{f} #{i + 1}: zu wenig Volumen (n={recips or 'unbekannt'}) — naechste Pruefung Sonntag"); continue
            print(f"{f} #{i + 1}: faellig fuer Herausforderer — Roadmap marketing/workflows/02-specs/2026-09-16-ab-roadmap.md, Bau nach seinem 'ja'")
    print("(nur gelesen — kein Flow angelegt, nichts live gesetzt)")


def _nonull(x):
    """null-Felder aus GET-Antworten weglassen — ein PATCH mit null liest Klaviyo als Änderung (24.09., A/B-Start)."""
    if isinstance(x, dict): return {k: _nonull(v) for k, v in x.items() if v is not None}
    return [_nonull(v) for v in x] if isinstance(x, list) else x


def _set_live(fid):
    """Flow-ID direkt auf 'live' (Mail-Actions + A/B-Experimente); von live() und go() genutzt. Gibt Zahl gestarteter A/B-Tests zurück."""
    for a in pages(f"/api/flows/{fid}/flow-actions"):
        if a["attributes"].get("action_type") == "SEND_EMAIL" and a["attributes"].get("status") != "live":
            api("PATCH", f"/api/flow-actions/{a['id']}", {"data": {"type": "flow-action", "id": a["id"], "attributes": {"status": "live"}}})
    api("PATCH", f"/api/flows/{fid}", {"data": {"type": "flow", "id": fid, "attributes": {"status": "live"}}})
    e = 0
    for a in pages(f"/api/flows/{fid}/flow-actions"):                                   # A/B-Experimente starten (16.09.): nur per PATCH der Definition
        d = a["attributes"]["definition"]
        if d.get("type") == "ab-test" and d["data"].get("experiment_status") != "live":
            d["data"]["experiment_status"] = "live"
            body = {"data": {"type": "flow-action", "id": a["id"], "attributes": {"definition": d}}}
            r = api("PATCH", f"/api/flow-actions/{a['id']}", body, soft=True)
            if "error" in r:   # 24.09.: 400 „Cannot update the main action while the experiment is live“ — GET liefert metric_filters: null (Kappe), PATCH liest das als Änderung
                body["data"]["attributes"]["definition"] = _nonull(d)
                r = api("PATCH", f"/api/flow-actions/{a['id']}", body, soft=True)
            if "error" in r: print(f"  ! A/B {a['id']} bleibt draft (Flow sendet Variante A): {r['error'][:160]}"); continue
            e += 1
    return e


def live(f):
    """Flow UND seine Mail-Actions auf 'live' (seine Ansage 15.09.: „mach die klaviyo mails live“). Vorher: WELCOME15 auf 15 % (discount.py)."""
    fid = (json.loads(IDS.read_text()) if IDS.is_file() else {}).get("flows", {}).get(f) or sys.exit(f"{f}: keine Flow-ID in state/klaviyo/ids.json")
    e = _set_live(fid)
    print(f"{f} -> live ({e} A/B-Tests gestartet): https://www.klaviyo.com/flow/{fid}/edit")


def selftest():
    """Ohne Netz: Mini-Specs + Mini-PLAN mit Split-Baum (2 Pfade, gleicher Mail-Key 'b') durch flow() bauen, prüfen: JSON
    serialisierbar, alle temporary_ids eindeutig, next_if_true/false zeigen auf vorhandene IDs, additional_filters gesetzt
    (Kappe, da 'a'/'b' nicht in NO_SMART) — Pre-Mortem #5 (flows-verhalten.md §7): zwei send-Actions desselben Keys duerfen
    sich nicht die temporary_id teilen."""
    save_m, save_plan, save_name = dict(M), dict(PLAN), dict(NAME)
    M.update({"a": {"flow": "a", "subject": "A", "preview": "a"}, "b": {"flow": "b", "subject": "B", "preview": "b"}})
    NAME["selftest"] = "Selftest"
    PLAN["selftest"] = (("metric", "Placed Order"), [
        (0, "minutes", "a"),
        ("split", "x", [("Placed Order", "greater-than-or-equal", 1, {"type": "date", "operator": "alltime"})],
          [(1, "days", "b")], [(2, "days", "b")])
    ], ["Placed Order"], {"duration": 0, "unit": "alltime"})
    mids = {n: f"id:{n}" for n in METRICS}
    f = flow("selftest", {"NL a": "t:a", "NL b": "t:b"}, mids, "list:1")
    json.dumps(f)   # muss serialisierbar sein
    acts = f["data"]["attributes"]["definition"]["actions"]
    tids_seen = [a["temporary_id"] for a in acts]
    assert len(tids_seen) == len(set(tids_seen)), "temporary_id doppelt"
    ids_all = set(tids_seen)
    split = next(a for a in acts if a["type"] == "conditional-split")
    assert split["links"]["next_if_true"] in ids_all and split["links"]["next_if_false"] in ids_all, "next_if_true/false zeigt ins Leere"
    sends_b = [a for a in acts if a["type"] == "send-email" and a["data"]["message"]["template_id"] == "t:b"]
    assert len(sends_b) == 2 and sends_b[0]["temporary_id"] != sends_b[1]["temporary_id"], "Mail-Key 'b' braucht zwei eigene send-Actions (ein Pfad je Zweig)"
    assert all(a["data"]["message"]["additional_filters"] for a in acts if a["type"] == "send-email"), "additional_filters (Kappe) fehlt"
    M.clear(); M.update(save_m); PLAN.clear(); PLAN.update(save_plan); NAME.clear(); NAME.update(save_name)
    print(f"selftest ok: {len(acts)} actions, {len(ids_all)} eindeutige temporary_ids, Split-Baum + additional_filters ok")


if __name__ == "__main__":
    a = sys.argv[1:]; cmd = a[0] if a else ""
    if cmd == "--selftest": selftest(); sys.exit(0)
    only = a[a.index("--flows") + 1].split(",") if "--flows" in a else None
    bad = [f for f in only or [] if f not in PLAN]
    if bad: sys.exit(f"unbekannte Flows: {', '.join(bad)} — moeglich: {', '.join(PLAN)}")
    if cmd == "check": check()
    elif cmd == "plan": plan(only)
    elif cmd == "apply": apply(only, a[a.index("--list-id") + 1] if "--list-id" in a else None)
    elif cmd == "sync": sync(only)
    elif cmd == "abstatus": abstatus()
    elif cmd == "abreport": abreport()
    elif cmd == "abloop":
        if "--dry" not in a: sys.exit("abloop nur mit --dry: klaviyo.py abloop --dry (baut/schaltet nichts, nur Liste)")
        abloop()
    elif cmd == "recreate": recreate(only, a[a.index("--list-id") + 1] if "--list-id" in a else None, "--draft" in a)
    elif cmd == "go": go(only)
    elif cmd == "live" and len(a) > 1: live(a[1])
    else: print(__doc__); sys.exit(2)
