#!/usr/bin/env python3
"""Flow-Mails fuer Nora Lanelle — Bausteine, die per JSON zu einer Mail werden. 11.09.2026, Fassung 2
(seine Ansage: "make a banger template ... easy readable and tldr with strong messaging branded ...
work on it over and over").

    .venv/bin/python bin/flows.py build [SPEC.json]   HTML + PNG + Custom-Liquid-Section je Mail -> marketing/workflows/04-output/flows/
    .venv/bin/python bin/flows.py send [SPEC.json]    die PNGs an Telegram (je Mail eine Nachricht)

Typo-System (600 px):  Eyebrow 10 px / .34em Sperrung / Grossbuchstaben  ·  Headline Serife 40-48 px  ·  Lauftext 15 px / 1.65
·  Labels 11 px gesperrt  ·  Knopf 12 px gesperrt, Grossbuchstaben.  Farben: Tinte #141210, Nebel #6b6560, Linie #e5e0d8,
Papier #fbfaf8, Karte #f4f1ec.  Serife Didot/Bodoni/Georgia (Mailclients), Sans Helvetica/Arial.
Regeln aus Maxwell/Hustler: Hero = Headline + 1 Satz + Knopf auf dem Bild; ein Knopf je Sektion; Fuss mit
Kollektionen; nichts behaupten, was nicht auf der Seite steht; keine erfundenen Bewertungen.
Bausteine (type): hero (implizit), eyebrow, headline, text, bullets (mit Icons), list, products, facts (mit Icons),
tile, looks, collections, table, proof (nur echt), code, closing, statement, spacer.
"""
import re, html, json, pathlib, subprocess, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "marketing/workflows/04-output/flows"


def preview_fill(s):
    """Klaviyo-Tags in der PNG-Vorschau durch Beispielwerte ersetzen — nie im HTML fuer Klaviyo selbst
    (sein Fund 20.09.: {% coupon_code %} lief roh in der Vorschau). {% for %}/{% endfor %} raus (eine Beispielzeile
    bleibt stehen), {{ item.* }} durch Beispielprodukt/-preis, jedes uebrige {{ }} durch generischen Text."""
    stamp = datetime.date.today().strftime("%m%d")
    s = re.sub(r"\{%\s*coupon_code\s*'([^']+)'\s*%\}", lambda m: f"{m.group(1)}-{stamp}-K7PQ2", s)
    s = s.replace("{% unsubscribe_link %}", "Unsubscribe")   # --klaviyo ersetzt den ganzen Anker durch nur den Tag
    s = re.sub(r"\{%[^%]*%\}", "", s)   # Rest (for/endfor, evtl. weitere) — nicht in der Vorschau
    item_examples = {"ProductName": "The Wide-Leg Trouser", "product.title": "The Wide-Leg Trouser",
                      "Quantity": "1", "quantity|default:1": "1", "RowTotal|floatformat:0": "89",
                      "line_price|floatformat:0": "89", "variant_title|default:'Size as chosen'": "Size M"}
    for k, v in item_examples.items():
        s = s.replace("{{ item." + k + " }}", v)
    s = re.sub(r"\{\{\s*event\.extra\.total_price\|floatformat:0\s*\}\}", "268", s)
    s = re.sub(r"\{\{\s*event\.extra\|lookup:'\$value'\|floatformat:0\s*\}\}", "268", s)
    s = re.sub(r"\{\{\s*[^}]*\}\}", "Example", s)   # Rest (URLs in href/src etc.) — nicht sichtbar oder Fallback
    return s
P = json.loads((ROOT / "state/products-email.json").read_text())
MAILIMG = json.loads((ROOT / "state/mail-images.json").read_text())
CDN = "https://cdn.shopify.com/s/files/1/0794/1793/4012/files/"
HERO = {"street": CDN + "campaign-hero_05a39e51-d204-45ab-b05f-98bf22bdf12f.png?width=1200",
        "room": CDN + "campaign-hero-3_96bf127c-4a8a-4cba-b181-73dd22047fa5.png?width=1200",
        "terrace": CDN + "campaign-hero-4_49d8a389-6a08-49db-a7c6-507140a45a19.png?width=1200",
        "persona": MAILIMG["01"], "persona2": MAILIMG["03"], "persona3": MAILIMG["04"], "persona4": MAILIMG["06"],
        "persona5": MAILIMG["09"], "closeup": MAILIMG["05"],
        "dress": MAILIMG["10"], "look-town-coat": MAILIMG["11"], "look-off-duty": MAILIMG["12"],
        "look-after-dark": MAILIMG["13"], "look-soft-autumn": MAILIMG["14"], "autumn": MAILIMG["15"],
        "vibe1": MAILIMG["21"], "vibe2": MAILIMG["22"], "vibe3": MAILIMG["23"], "vibe4": MAILIMG["24"], "vibe5": MAILIMG["25"], "vibe6": MAILIMG["26"]}
SHOP = "https://nora-lanelle.com"
SERIF = "Didot, 'Bodoni 72', 'Bodoni MT', Georgia, 'Times New Roman', serif"
SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"
INK, MUTED, RULE, PAPER, CARD, WHITE = "#141210", "#6b6560", "#e5e0d8", "#fbfaf8", "#f4f1ec", "#ffffff"
EYE = f"font-family:{SANS};font-size:10px;letter-spacing:.34em;text-transform:uppercase;color:{MUTED}"
LAB = f"font-family:{SANS};font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:{MUTED}"
BODY = f"font-family:{SANS};font-size:15px;line-height:1.65;color:{INK}"

ICONS = {  # duenne Linien-Icons, 24er Raster, currentColor
    "waist": '<path d="M9 3h6l-1.5 6H10.5z"/><path d="M10.5 9 6 20h12L13.5 9"/><path d="M8 14h8"/>',
    "sleeve": '<path d="M5 4h6l3 6-4 10H6L4 10z"/><path d="M6 20h4"/>',
    "knit": '<path d="M4 8c2-3 4-3 6 0s4 3 6 0 4-3 6 0M4 14c2-3 4-3 6 0s4 3 6 0 4-3 6 0"/>',
    "ship": '<path d="M3 7h11v9H3zM14 10h4l3 3v3h-7z"/><circle cx="7" cy="18" r="1.5"/><circle cx="17" cy="18" r="1.5"/>',
    "return": '<path d="M4 9h11a4 4 0 0 1 0 8H9"/><path d="M8 5 4 9l4 4"/>',
    "clock": '<circle cx="12" cy="12" r="8"/><path d="M12 7v5l3 2"/>',
    "reply": '<path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v7a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 3.5V16A2.5 2.5 0 0 1 4 13.5z"/>',
    "made": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 15l5-5 4 4 3-3 6 6"/>',
    "tag": '<path d="M3 12V4h8l9 9-8 8z"/><circle cx="7.5" cy="8.5" r="1.5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>',
    "palette": '<circle cx="7" cy="12" r="3.2"/><circle cx="14" cy="8.5" r="3.2"/><circle cx="16" cy="16" r="3.2"/>',
    "layers": '<path d="M12 4 3 9l9 5 9-5z"/><path d="M3 14l9 5 9-5"/>',
    "care": '<path d="M12 3c3 4 6 7.5 6 11a6 6 0 0 1-12 0c0-3.5 3-7 6-11z"/>',
}


def icon(name, size=22, color=INK):
    d = ICONS.get(name, ICONS["check"])
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.4" '
            f'stroke-linecap="round" stroke-linejoin="round" style="display:block">{d}</svg>')


def img_for(kind):
    if kind.startswith("product:"):
        h = kind.split(":", 1)[1]
        return P[h]["img"].split("?")[0] + "?width=1200"
    return HERO.get(kind, HERO["street"])


def vml_open(img, h, w=600, color="#2a2623"):
    """Outlook-Fallback fuer Hintergrundbilder (Cerberus, Recherche 12.09.). Nur Outlook Windows liest das."""
    return (f'<!--[if gte mso 9]><v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width:{w}px;height:{h}px">'
            f'<v:fill type="frame" src="{img}" color="{color}"/><v:textbox inset="0,0,0,0"><![endif]-->')


VML_CLOSE = '<!--[if gte mso 9]></v:textbox></v:rect><![endif]-->'


def btn(text, url, dark=True, full=True, pad="15px 26px"):
    bg, fg, bd = (INK, WHITE, INK) if dark else (WHITE, INK, INK)
    w = 'width="100%"' if full else ""
    return (f'<table role="presentation" {w} cellpadding="0" cellspacing="0" style="{"width:100%" if full else ""}"><tr><td align="center" bgcolor="{bg}" style="background:{bg};border:1px solid {bd}">'
            f'<a href="{url}" style="display:block;padding:{pad};color:{fg};text-decoration:none;font-family:{SANS};font-size:12px;letter-spacing:.26em;text-transform:uppercase;font-weight:600;white-space:nowrap">{html.escape(text)}</a></td></tr></table>')


def ghost(text, url, arrow=True):
    return f'<a href="{url}" style="{LAB};color:{INK};text-decoration:none;border-bottom:1px solid {INK};padding-bottom:3px">{html.escape(text)}{" &nbsp;&rarr;" if arrow else ""}</a>'


def spacer(h=18):
    return f'<tr><td style="height:{h}px;line-height:{h}px;font-size:0">&nbsp;</td></tr>'


def head_row():
    return (f'<tr><td align="center" style="padding:30px 0 6px"><a href="{SHOP}" style="text-decoration:none;color:{INK};font-family:{SERIF};font-size:30px;letter-spacing:.08em">Nora Lanelle</a></td></tr>'
            f'<tr><td align="center" class="trust" style="padding:0 0 22px;{EYE};letter-spacing:.2em;white-space:nowrap">Easy returns, 30 days &nbsp;·&nbsp; Delivery 7–10 days &nbsp;·&nbsp; Shipping on us from $150</td></tr>')


def hero(kind, headline, sub, cta1, url, eyebrow="", cta2=None, h=680):
    img = img_for(kind)
    if kind.startswith("product:"):
        return f"""<tr><td style="padding:0"><a href="{url}"><img src="{img}" width="600" alt="" style="display:block;width:100%;height:auto;background:{CARD}"></a></td></tr>
{('<tr><td align="center" style="padding:30px 40px 6px;' + EYE + '">' + html.escape(eyebrow) + '</td></tr>') if eyebrow else spacer(26)}
<tr><td align="center" style="padding:0 40px 10px;font-family:{SERIF};font-size:40px;line-height:1.05;color:{INK}">{html.escape(headline)}</td></tr>
<tr><td align="center" style="padding:0 56px 22px;{BODY};color:{MUTED}">{html.escape(sub)}</td></tr>
<tr><td align="center" style="padding:0 40px 30px"><table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto"><tr><td>{btn(cta1, url, dark=True, full=False)}</td></tr></table></td></tr>"""
    return f"""<tr><td style="padding:0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td class="hero" background="{img}" bgcolor="#3a3531" valign="bottom" style="background-color:#3a3531;background-image:url('{img}');background-position:center top;background-size:cover;background-repeat:no-repeat;height:{h}px">
{vml_open(img, h, 600, "#3a3531")}<div class="ov" style="background:linear-gradient(180deg,rgba(0,0,0,0) 48%,rgba(0,0,0,.66) 100%);padding:{h - 290}px 36px 36px">
  <div style="font-family:{SANS};font-size:10px;letter-spacing:.34em;text-transform:uppercase;color:#ffffff;opacity:.85;padding-bottom:12px">{html.escape(eyebrow or "Nora Lanelle")}</div>
  <div class="h1" style="font-family:{SERIF};font-size:44px;line-height:1.02;color:#ffffff;letter-spacing:.005em">{html.escape(headline).replace(chr(10), "<br>")}</div>
  <div style="height:12px"></div>
  <div style="font-family:{SANS};font-size:14px;line-height:1.55;color:#ffffff;opacity:.94;max-width:420px">{html.escape(sub)}</div>
  <div style="height:22px"></div>
  <table role="presentation" cellpadding="0" cellspacing="0"><tr><td class="stk">{btn(cta1, url, dark=False, full=False)}</td>{('<td class="stk cta2" style="padding-left:16px;vertical-align:middle;white-space:nowrap"><a href="' + (cta2[1] if isinstance(cta2, (list, tuple)) else url) + '" style="font-family:' + SANS + ';font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#ffffff;text-decoration:none;border-bottom:1px solid rgba(255,255,255,.7);padding-bottom:3px">' + html.escape(cta2[0] if isinstance(cta2, (list, tuple)) else cta2) + ' &rarr;</a></td>') if cta2 else ''}</tr></table>
</div>{VML_CLOSE}</td></tr></table></td></tr>"""


def eyebrow_row(text, pad="36px 40px 8px"):
    return f'<tr><td align="center" style="padding:{pad};{EYE}">{html.escape(text)}</td></tr>'


def headline_row(text, size=30, pad="0 40px 10px"):
    return f'<tr><td align="center" style="padding:{pad};font-family:{SERIF};font-size:{size}px;line-height:1.1;color:{INK}">{html.escape(text)}</td></tr>'


def text_block(lines, muted=False, pad="6px 56px 30px"):
    body = "<br>".join(html.escape(l) for l in lines)
    return f'<tr><td align="center" style="padding:{pad};{BODY};{"color:" + MUTED if muted else ""}">{body}</td></tr>'


def statement(text, pad="10px 48px 26px"):
    return f'<tr><td align="center" style="padding:{pad};font-family:{SERIF};font-size:22px;line-height:1.35;color:{INK}">{html.escape(text)}</td></tr>'


def bullets(items, icons=None):
    """Seine Ansage 11.09.: „make statements not yap their ear off“ — Label klein, der Satz gross und in Tinte."""
    icons = icons or ["waist", "sleeve", "knit"]
    rows = ""
    for it, ic in zip(items, icons):
        k, _, v = it.partition(" — ")
        rows += (f'<tr><td width="44" valign="top" style="padding:16px 0 0">{icon(ic)}</td>'
                 f'<td valign="top" style="padding:14px 0 16px 6px;border-bottom:1px solid {RULE}"><div style="{LAB};font-size:10px">{html.escape(k)}</div>'
                 f'<div style="font-family:{SERIF};font-size:21px;line-height:1.25;color:{INK};padding-top:6px">{html.escape(v)}</div></td></tr>')
    return f'<tr><td style="padding:26px 40px 22px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>'


def products(handles, label="", cta="", show_compare=True, dark=False):
    """Auf dem Handy eine Reihe zum Wischen (seine Ansage 11.09.: „make it left to right scrollable“), am Desktop 3 nebeneinander."""
    n = min(3, len(handles)); cards = ""
    for hd in handles[:3]:
        x = P[hd]; img = x["img"].split("?")[0] + "?width=500"
        cmp = f' <span style="text-decoration:line-through;opacity:.55">${x["compare"]:.0f}</span>' if show_compare and x.get("compare") else ""
        cards += f"""<div class="card" style="display:inline-block;vertical-align:top;width:{100 // n}%;white-space:normal;text-align:center;box-sizing:border-box;padding:0 6px">
<a href="{x['url']}" style="text-decoration:none;color:{INK};display:block"><img src="{img}" width="176" alt="{html.escape(x['title'])}" style="display:block;width:100%;height:auto;margin:0 auto;background:{CARD}">
<div style="font-family:{SERIF};font-size:16px;line-height:1.3;color:{INK};padding-top:12px">{html.escape(x['title'])}</div>
<div style="font-family:{SANS};font-size:12px;letter-spacing:.06em;color:{MUTED};padding:5px 0 {"12px" if cta else "0"}">${x['price']:.0f}{cmp}</div></a>
{btn(cta, x['url'], dark=dark, pad="12px 10px") if cta else ""}</div>"""
    lab = f'<div style="{EYE};padding:0 0 18px;text-align:center">{html.escape(label)}</div>' if label else ""
    return f'<tr><td style="padding:30px 28px 26px">{lab}<div class="scroll" style="white-space:nowrap;font-size:0;line-height:0;width:0;min-width:100%">{cards}</div></td></tr>'


def facts(items, icons=None):
    icons = icons or ["ship", "return", "clock"]
    cells = ""
    for it, ic in zip(items[:3], icons):
        k, _, v = it.partition(" — ")
        cells += (f'<td width="33%" valign="top" align="center" style="padding:0 4px"><table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto"><tr><td>{icon(ic, 24)}</td></tr></table>'
                  f'<div class="f" style="font-family:{SERIF};font-size:17px;color:{INK};padding-top:10px">{html.escape(v or k)}</div><div style="{LAB};font-size:10px;padding-top:5px">{html.escape(k if v else "")}</div></td>')
    return (f'<tr><td style="padding:6px 28px 30px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{CARD}" style="background:{CARD};">'
            f'<tr><td style="padding:24px 10px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{cells}</tr></table></td></tr></table></td></tr>')


def tile(kind, label, headline, cta, url, h=380):
    img = img_for(kind)
    return f"""<tr><td style="padding:8px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td background="{img}" bgcolor="#2a2623" valign="bottom" style="background-color:#2a2623;background-image:url('{img}');background-position:center;background-size:cover;background-repeat:no-repeat;height:{h}px">
{vml_open(img, h)}<div style="background:linear-gradient(180deg,rgba(0,0,0,0) 45%,rgba(0,0,0,.55) 100%);padding:{h - 160}px 36px 34px">
<div style="font-family:{SANS};font-size:10px;letter-spacing:.34em;text-transform:uppercase;color:#ffffff;opacity:.85">{html.escape(label)}</div>
<div class="h2" style="font-family:{SERIF};font-size:36px;line-height:1.05;color:#ffffff;padding:8px 0 18px">{html.escape(headline)}</div>
<table role="presentation" cellpadding="0" cellspacing="0"><tr><td>{btn(cta, url, dark=False, full=False)}</td></tr></table></div>{VML_CLOSE}</td></tr></table></td></tr>"""


def looks(items, cta_all=None, label=""):
    cells = ""
    for i, (kind, name, url) in enumerate(items[:4]):
        img = img_for(kind)
        cells += f"""<td width="50%" valign="top" style="padding:{'0 5px 10px 0' if i % 2 == 0 else '0 0 10px 5px'}">
<a href="{url}" style="text-decoration:none"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td class="lk" background="{img}" bgcolor="#2a2623" valign="bottom" style="background-color:#2a2623;background-image:url('{img}');background-position:center 20%;background-size:cover;background-repeat:no-repeat;height:320px;">
<div class="lkov" style="background:linear-gradient(180deg,rgba(0,0,0,0) 55%,rgba(0,0,0,.52) 100%);padding:246px 18px 18px;">
<div class="h3" style="font-family:{SERIF};font-size:24px;color:#ffffff">{html.escape(name)}</div></div></td></tr></table></a></td>"""
        if i == 1: cells += "</tr><tr>"
    more = f'<tr><td colspan="2" align="center" style="padding:14px 0 0"><table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto"><tr><td>{btn(cta_all[0], cta_all[1], dark=False, full=False)}</td></tr></table></td></tr>' if cta_all else ""
    lab = f'<tr><td colspan="2" align="center" style="padding:0 0 18px;{EYE}">{html.escape(label)}</td></tr>' if label else ""
    return f'<tr><td style="padding:{"30px" if label else "6px"} 28px 30px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{lab}<tr>{cells}</tr>{more}</table></td></tr>'


def collections(items, label=""):
    links = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join(ghost(n, u) for n, u in items)
    lab = f'<div style="{EYE};padding-bottom:16px">{html.escape(label)}</div>' if label else ""
    return f'<tr><td align="center" style="padding:6px 30px 30px">{lab}{links}</td></tr>'


def table2(rows, left="", right=""):
    head = f'<tr><td style="padding:10px 12px;{LAB};font-size:10px">{html.escape(left)}</td><td style="padding:10px 12px;{LAB};font-size:10px">{html.escape(right)}</td></tr>' if left else ""
    body = "".join(f'<tr><td width="46%" valign="top" style="padding:12px;border-top:1px solid {RULE};{BODY};font-size:13px;color:{MUTED}">{html.escape(q)}</td>'
                   f'<td valign="top" style="padding:12px;border-top:1px solid {RULE};{BODY};font-size:13px"><b>{html.escape(a)}</b></td></tr>' for q, a in rows)
    return f'<tr><td style="padding:6px 30px 26px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {RULE};">{head}{body}</table></td></tr>'


def infolist(items):
    rows = "".join(f'<tr><td width="34" valign="top" style="padding:10px 0">{icon("check", 22)}</td><td valign="top" style="padding:10px 0 10px 8px;{BODY};font-size:14px"><b>{html.escape(it.partition(" — ")[0])}</b>{(" — " + html.escape(it.partition(" — ")[2])) if " — " in it else ""}</td></tr>' for it in items)
    return f'<tr><td style="padding:6px 40px 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>'


def proof(text, who=""):
    tail = f'<div style="{LAB};padding-top:12px;font-style:normal">{html.escape(who)}</div>' if who else ""
    return f'<tr><td align="center" style="padding:10px 48px 30px;font-family:{SERIF};font-size:21px;line-height:1.4;color:{INK};font-style:italic">“{html.escape(text)}”{tail}</td></tr>'


def reviews(items, label=""):
    """Kurze Stimmen nebeneinander. PLATZHALTER bis echte da sind (seine Ansage 12.09., 07:35: Testaufbau, wird so nicht
    veroeffentlicht) — Spec-Feld placeholder_proof: true, build() warnt."""
    cells = ""
    for text, who in items[:3]:
        cells += (f'<td class="col" width="{100 // len(items[:3])}%" valign="top" style="padding:0 6px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{CARD}" style="background:{CARD}"><tr><td style="padding:20px 18px 18px">'
                  f'<div style="font-family:{SANS};font-size:11px;letter-spacing:.2em;color:{INK}">★★★★★</div>'
                  f'<div style="font-family:{SERIF};font-size:16px;line-height:1.35;color:{INK};padding:10px 0 12px">“{html.escape(text)}”</div>'
                  f'<div style="{LAB};font-size:10px">{html.escape(who)}</div></td></tr></table></td>')
    lab = f'<tr><td align="center" style="padding:0 0 16px;{EYE}">{html.escape(label)}</td></tr>' if label else ""
    return f'<tr><td style="padding:26px 28px 26px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{lab}<tr>{cells}</tr></table></td></tr>'


def codeblock(head, text, code, cta, url, note="", eyebrow="Your first order"):
    return f"""<tr><td style="padding:8px 28px 34px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{INK}" style="background:{INK};"><tr><td align="center" style="padding:34px 32px 32px">
<div style="{EYE};color:#ffffff;opacity:.7">{html.escape(eyebrow)}</div>
<div style="font-family:{SERIF};font-size:30px;line-height:1.12;color:#ffffff;padding-top:8px">{html.escape(head)}</div>
<div style="font-family:{SANS};font-size:14px;line-height:1.6;color:#ffffff;opacity:.85;padding:12px 0 20px;max-width:400px;margin:0 auto">{html.escape(text)}</div>
<div style="font-family:{SANS};font-size:22px;letter-spacing:.28em;text-transform:uppercase;color:#ffffff;padding:2px 0 22px">{html.escape(code)}</div>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto"><tr><td>{btn(cta, url, dark=False, full=False)}</td></tr></table>
{('<div style="font-family:' + SANS + ';font-size:11px;color:#ffffff;opacity:.6;padding-top:14px">' + html.escape(note) + '</div>') if note else ''}
</td></tr></table></td></tr>"""


def closing(kind, headline, cta, url, sub=""):
    img = img_for(kind)
    subhtml = f'<div style="font-family:{SANS};font-size:14px;color:#ffffff;opacity:.9;padding-top:10px">{html.escape(sub)}</div>' if sub else ""
    return f"""<tr><td style="padding:0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td background="{img}" bgcolor="#2a2623" valign="bottom" align="left" style="background-color:#2a2623;background-image:url('{img}');background-position:center;background-size:cover;background-repeat:no-repeat;height:460px">
{vml_open(img, 460)}<div style="background:linear-gradient(180deg,rgba(0,0,0,.05) 40%,rgba(0,0,0,.6) 100%);padding:250px 36px 40px">
<div class="h2" style="font-family:{SERIF};font-size:38px;line-height:1.08;color:#ffffff;max-width:380px">{html.escape(headline).replace(chr(10), "<br>")}</div>{subhtml}
<div style="height:20px"></div>
<table role="presentation" cellpadding="0" cellspacing="0"><tr><td>{btn(cta, url, dark=False, full=False)}</td></tr></table></div>{VML_CLOSE}</td></tr></table></td></tr>"""


UNSUB = '<a href="{{ unsubscribe_url }}" style="color:' + MUTED + '">Unsubscribe</a>'   # Shopify Email; --klaviyo setzt {% unsubscribe_link %}


TRUST = ["US brand, Wyoming", "Priced in USD", "Easy returns, 30 days"]   # "a person answers" nicht extra unten (seine Ansage 13.09.)


def trustrow(items=None):
    items = items or TRUST
    cells = "".join(f'<td align="center" valign="top" style="padding:0 6px;{LAB};font-size:10px;line-height:1.5;color:{INK}">{html.escape(t)}</td>' for t in items)
    return (f'<tr><td style="padding:26px 28px 0;border-top:1px solid {RULE}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{cells}</tr></table></td></tr>')


def foot(line="Made, not photographed."):
    links = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join(ghost(n, SHOP + u, arrow=False) for n, u in [("New In", "/collections/new-in"), ("Coats", "/collections/outerwear"), ("Knitwear", "/collections/knitwear"), ("Dresses", "/collections/dresses"), ("Looks", "/pages/shop-the-looks")])
    return f"""<tr><td align="center" style="padding:30px 30px 8px;{EYE}">Shop by collection</td></tr>
<tr><td align="center" style="padding:0 30px 26px">{links}</td></tr>
<tr><td align="center" style="padding:0 30px 36px;font-family:{SANS};font-size:11px;line-height:1.9;color:{MUTED}">{html.escape(line)}<br>Nora Lanelle · a US brand · Northbound Systems LLC · 5830 E 2nd St, Ste 7000, Casper, WY 82609, USA<br>{UNSUB} &nbsp;·&nbsp; <a href="{SHOP}/policies/privacy-policy" style="color:{MUTED}">Privacy</a></td></tr>"""


def plain(m):
    body = html.escape(re.sub(r"^(\w+)\nNora Lanelle$", r"\1\nNora Lanelle, Wyoming, USA", m["text"], flags=re.M)).replace("\n", "<br>")
    if m.get("link"):
        body = body.replace(html.escape(m["link"]), f'<a href="{m["link"]}" style="color:{INK}">{html.escape(m["link"])}</a>')
    body = re.sub(r"\{[%{].*?[%}]\}", lambda t: t.group(0).replace("&#x27;", "'").replace("&quot;", '"').replace("&amp;", "&"), body)   # Klaviyo-Tags unescaped lassen (15.09.: coupon_code in Textmail)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(m['subject'])}</title></head>
<body style="margin:0;padding:0;background:#ffffff"><div style="display:none;max-height:0;overflow:hidden;font-size:1px;color:#ffffff">{html.escape(m.get('preview',''))}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center"><table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px">
<tr><td style="padding:28px 24px 40px;{BODY}">{body}</td></tr></table></td></tr></table></body></html>"""


# --- Formate (seine Ansage 12.09., 07:33: "they all look way too similar try different formats different layouts") ---

def codebar(text, url):
    return (f'<tr><td align="center" bgcolor="{INK}" style="background:{INK};padding:12px 20px;font-family:{SANS};font-size:11px;letter-spacing:.22em;'
            f'text-transform:uppercase;color:#ffffff"><a href="{url}" style="color:#ffffff;text-decoration:none">{html.escape(text)}</a></td></tr>')


def hero_text(headline, sub, cta1, url, eyebrow="", cta2=None):
    """Kein Bild: Typo-Hero auf Papier."""
    c2 = (f'<td class="stk cta2" style="padding-left:16px;vertical-align:middle;white-space:nowrap">{ghost(cta2[0], cta2[1])}</td>') if cta2 else ""
    eye = f'<tr><td align="center" style="padding:26px 40px 10px;{EYE}">{html.escape(eyebrow)}</td></tr>' if eyebrow else spacer(26)
    return (eye +
            f'<tr><td align="center" class="h1" style="padding:0 40px 14px;font-family:{SERIF};font-size:44px;line-height:1.04;color:{INK}">{html.escape(headline).replace(chr(10), "<br>")}</td></tr>'
            f'<tr><td align="center" style="padding:0 64px 24px;{BODY};color:{MUTED}">{html.escape(sub)}</td></tr>'
            f'<tr><td align="center" style="padding:0 40px 30px"><table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto"><tr><td class="stk">{btn(cta1, url, dark=True, full=False)}</td>{c2}</tr></table></td></tr>')


def hero_split(kind, headline, sub, cta1, url, eyebrow="", code=None):
    """Editorial: Bild links, Textkarte rechts."""
    img = img_for(kind)
    codehtml = (f'<div style="padding-top:18px;font-family:{SANS};font-size:18px;letter-spacing:.26em;text-transform:uppercase;color:{INK}">{html.escape(code)}</div>') if code else ""
    return f"""<tr><td style="padding:0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td class="col" width="50%" valign="top" style="padding:0"><a href="{url}"><img src="{img}" width="300" alt="" style="display:block;width:100%;height:auto;background:{CARD}"></a></td>
<td class="col colp" width="50%" valign="middle" bgcolor="{CARD}" style="background:{CARD};padding:34px 28px">
<div style="{EYE}">{html.escape(eyebrow)}</div>
<div class="h2" style="font-family:{SERIF};font-size:34px;line-height:1.05;color:{INK};padding-top:10px">{html.escape(headline).replace(chr(10), "<br>")}</div>
<div style="{BODY};font-size:14px;color:{MUTED};padding-top:12px">{html.escape(sub)}</div>{codehtml}
<div style="padding-top:22px">{btn(cta1, url, dark=True, full=False, pad="14px 20px")}</div></td></tr></table></td></tr>"""


def hero_type(big, headline, sub, cta1, url, eyebrow=""):
    """Typografisch: Tinte, riesige Zahl."""
    return f"""<tr><td align="center" bgcolor="{INK}" style="background:{INK};padding:54px 40px 50px">
<div style="{EYE};color:#ffffff;opacity:.7">{html.escape(eyebrow)}</div>
<div style="font-family:{SERIF};font-size:150px;line-height:.95;color:#ffffff;letter-spacing:-.02em;padding-top:14px">{html.escape(big)}</div>
<div class="h2" style="font-family:{SERIF};font-size:32px;line-height:1.1;color:#ffffff;padding-top:14px">{html.escape(headline).replace(chr(10), "<br>")}</div>
<div style="font-family:{SANS};font-size:14px;line-height:1.55;color:#ffffff;opacity:.85;padding:14px 0 26px;max-width:380px;margin:0 auto">{html.escape(sub)}</div>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto"><tr><td>{btn(cta1, url, dark=False, full=False)}</td></tr></table></td></tr>"""


def band(kind, text="", cta=None, url="", h=300, pos="center 30%"):
    """Vollbreites Bild-Band als Uebergang: eine Zeile, optional ein Textlink. Seine Ansage 12.09., 08:45: mehr Hintergrund, Uebergaenge."""
    img = img_for(kind)
    inner = ""
    if text:
        inner += f'<div class="h2" style="font-family:{SERIF};font-size:30px;line-height:1.1;color:#ffffff;max-width:380px">{html.escape(text).replace(chr(10), "<br>")}</div>'
    if cta:
        inner += f'<div style="padding-top:14px"><a href="{url}" style="font-family:{SANS};font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#ffffff;text-decoration:none;border-bottom:1px solid rgba(255,255,255,.7);padding-bottom:3px">{html.escape(cta)} &rarr;</a></div>'
    return f"""<tr><td style="padding:0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td background="{img}" bgcolor="#2a2623" valign="bottom" style="background-color:#2a2623;background-image:url('{img}');background-position:{pos};background-size:cover;background-repeat:no-repeat;height:{h}px">
{vml_open(img, h)}<div style="background:linear-gradient(180deg,rgba(0,0,0,0) 40%,rgba(0,0,0,.55) 100%);padding:{h - 120}px 36px 32px">{inner}</div>{VML_CLOSE}</td></tr></table></td></tr>"""


def strip(kinds, h=220, urls=None):
    """Drei Bilder nebeneinander, kein Text — ein Atemzug zwischen zwei Bloecken."""
    cells = ""
    for i, k in enumerate(kinds[:3]):
        img = img_for(k); u = (urls or [SHOP + "/pages/shop-the-looks"] * 3)[i]
        cells += f'<td width="33%" style="padding:0 {"2px" if i == 1 else "0"}"><a href="{u}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td background="{img}" bgcolor="{CARD}" style="background-color:{CARD};background-image:url({img});background-position:center 20%;background-size:cover;background-repeat:no-repeat;height:{h}px;font-size:0">&nbsp;</td></tr></table></a></td>'
    return f'<tr><td style="padding:0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{cells}</tr></table></td></tr>'


def tone(text, sub="", bg=None, dark=False, eyebrow=""):
    """Farbige Textbank (Karte oder Tinte) als Uebergang mit einem Satz."""
    bg = bg or (INK if dark else CARD); fg = "#ffffff" if dark else INK; mu = "rgba(255,255,255,.75)" if dark else MUTED
    e = f'<div style="{EYE};{"color:#ffffff;opacity:.7" if dark else ""};padding-bottom:10px">{html.escape(eyebrow)}</div>' if eyebrow else ""
    sb = f'<div style="font-family:{SANS};font-size:14px;line-height:1.55;color:{mu};padding-top:10px;max-width:400px;margin:0 auto">{html.escape(sub)}</div>' if sub else ""
    return (f'<tr><td align="center" bgcolor="{bg}" style="background:{bg};padding:38px 40px">{e}'
            f'<div class="h2" style="font-family:{SERIF};font-size:28px;line-height:1.15;color:{fg}">{html.escape(text).replace(chr(10), "<br>")}</div>{sb}</td></tr>')


def split(kind, headline, text, cta, url, side="left", bg=None, eyebrow=""):
    """Bild links/rechts, Text daneben auf farbigem Band — alternierend einsetzen (Sézane, Jenni Kayne, NAP; Memo 12.09.)."""
    img = img_for(kind); bg = bg or CARD
    pic = f'<td class="col" width="50%" valign="top" style="padding:0"><a href="{url}"><img src="{img}" width="300" alt="" style="display:block;width:100%;height:auto;background:{CARD}"></a></td>'
    txt = (f'<td class="col colp" width="50%" valign="middle" bgcolor="{bg}" style="background-color:{bg};padding:30px 26px">'
           f'{("<div style=" + chr(34) + EYE + chr(34) + ">" + html.escape(eyebrow) + "</div>") if eyebrow else ""}'
           f'<div class="h2" style="font-family:{SERIF};font-size:28px;line-height:1.08;color:{INK};padding-top:{"8px" if eyebrow else "0"}">{html.escape(headline).replace(chr(10), "<br>")}</div>'
           f'<div style="{BODY};font-size:14px;color:{MUTED};padding-top:10px">{html.escape(text)}</div>'
           f'<div style="padding-top:16px">{ghost(cta, url)}</div></td>')
    cells = pic + txt if side == "left" else txt + pic
    return f'<tr><td style="padding:0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{cells}</tr></table></td></tr>'


def editorial(kind, text, cta, url, h=640):
    """Ein Bild (beschnitten auf h), ein Absatz (18–34 Woerter), ein Textlink — Toteme/Massimo Dutti."""
    img = img_for(kind)
    return (f'<tr><td style="padding:0"><a href="{url}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td background="{img}" bgcolor="{CARD}" style="background-color:{CARD};background-image:url(\'{img}\');background-position:center 25%;background-size:cover;background-repeat:no-repeat;height:{h}px;font-size:0">{vml_open(img, h, 600, CARD)}&nbsp;{VML_CLOSE}</td></tr></table></a></td></tr>'
            f'<tr><td align="center" style="padding:28px 70px 8px;{BODY};font-size:15px;color:{INK}">{html.escape(text)}</td></tr>'
            f'<tr><td align="center" style="padding:6px 40px 34px">{ghost(cta, url)}</td></tr>')


def fade(a=None, b=None, h=80):
    """Verlauf als Uebergang zwischen zwei Baendern; bgcolor traegt den Fallback."""
    a = a or WHITE; b = b or CARD
    return (f'<tr><td bgcolor="{b}" style="background-color:{b};background-image:linear-gradient(180deg,{a},{b});height:{h}px;font-size:0;line-height:0">'
            f'<!--[if gte mso 9]><v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width:600px;height:{h}px"><v:fill type="gradient" color="{a}" color2="{b}" angle="180"/></v:rect><![endif]-->&nbsp;</td></tr>')


def cartlist(handles, cta, url, label="Your bag"):
    """Wie die Warenkorb-Seite: Zeile je Teil, Summe, ein Knopf."""
    rows, total, was = "", 0, 0
    for hd in handles:
        x = P[hd]; img = x["img"].split("?")[0] + "?width=240"; total += x["price"]; was += x.get("compare") or x["price"]
        cmp = f' <span style="text-decoration:line-through;color:{MUTED}">${x["compare"]:.0f}</span>' if x.get("compare") else ""
        rows += (f'<tr><td width="96" style="padding:12px 0"><a href="{x["url"]}"><img src="{img}" width="84" alt="" style="display:block;width:84px;height:auto;background:{CARD}"></a></td>'
                 f'<td valign="middle" style="padding:12px 0 12px 14px;border-bottom:1px solid {RULE}"><div style="font-family:{SERIF};font-size:17px;color:{INK}">{html.escape(x["title"])}</div>'
                 f'<div style="{LAB};font-size:10px;padding-top:4px">Size as chosen</div></td>'
                 f'<td valign="middle" align="right" style="padding:12px 0 12px 8px;border-bottom:1px solid {RULE};font-family:{SANS};font-size:14px;color:{INK};white-space:nowrap">${x["price"]:.0f}{cmp}</td></tr>')
    rows += (f'<tr><td colspan="2" style="padding:16px 0 4px;{LAB}">Total, 45% Autumn Sale applied</td>'
             f'<td align="right" style="padding:16px 0 4px;font-family:{SERIF};font-size:22px;color:{INK}">${total:.0f} <span style="font-family:{SANS};font-size:12px;color:{MUTED};text-decoration:line-through">${was:.0f}</span></td></tr>')
    return (f'<tr><td style="padding:6px 40px 10px"><div style="{EYE};padding-bottom:6px">{html.escape(label)}</div><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>'
            f'<tr><td style="padding:14px 40px 30px">{btn(cta, url, dark=True, full=True, pad="17px 26px")}</td></tr>')


def kcart(cta, url, label="Your bag", source="shopify"):
    """Klaviyo-dynamisch (15.09.): die echten Teile aus dem Event — source "shopify" = Checkout Started (event.extra.line_items),
    source "cart" = unser Added-to-Cart-Event aus bin/pipeline/klaviyo_onsite.py (event.extra.Items). Verkettete |default:variable rendert Klaviyo NICHT (geprüft 15.09.)."""
    if source == "cart":
        img, title, size, qty, price, loop, total = ("{{ item.ImageURL }}", "{{ item.ProductName }}", "Size as chosen", "{{ item.Quantity }}", "{{ item.RowTotal|floatformat:0 }}",
                                                     "{% for item in event.extra.Items %}", "{{ event.extra|lookup:'$value'|floatformat:0 }}")
    else:
        img, title, size, qty, price, loop, total = ("{{ item.product.images.0.src }}", "{{ item.product.title }}", "{{ item.variant_title|default:'Size as chosen' }}", "{{ item.quantity|default:1 }}",
                                                     "{{ item.line_price|floatformat:0 }}", "{% for item in event.extra.line_items %}", "{{ event.extra.total_price|floatformat:0 }}")
    row = (f'<tr><td width="96" style="padding:12px 0"><img src="{img}" width="84" alt="" style="display:block;width:84px;height:auto;background:{CARD}"></td>'
           f'<td valign="middle" style="padding:12px 0 12px 14px;border-bottom:1px solid {RULE}"><div style="font-family:{SERIF};font-size:17px;color:{INK}">{title}</div>'
           f'<div style="{LAB};font-size:10px;padding-top:4px">{size} · {qty}</div></td>'
           f'<td valign="middle" align="right" style="padding:12px 0 12px 8px;border-bottom:1px solid {RULE};font-family:{SANS};font-size:14px;color:{INK};white-space:nowrap">${price}</td></tr>')
    rows = loop + row + "{% endfor %}"
    rows += (f'<tr><td colspan="2" style="padding:16px 0 4px;{LAB}">Total, 45% Autumn Sale applied</td>'
             f'<td align="right" style="padding:16px 0 4px;font-family:{SERIF};font-size:22px;color:{INK}">${total}</td></tr>')
    return (f'<tr><td style="padding:6px 40px 10px"><div style="{EYE};padding-bottom:6px">{html.escape(label)}</div><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>'
            f'<tr><td style="padding:14px 40px 30px">{btn(cta, url, dark=True, full=True, pad="17px 26px")}</td></tr>')


def countdown(head, code, sub, cta, url, hours):
    """Code groß, Frist darunter (seine Ansage 15.09.: „code again bigger and expires in 48h“). `code` darf ein Klaviyo-Tag sein."""
    return (f'<tr><td align="center" style="padding:30px 40px 8px;{EYE}">{html.escape(head)}</td></tr>'
            f'<tr><td align="center" style="padding:0 40px 6px;font-family:{SERIF};font-size:54px;letter-spacing:.06em;line-height:1;color:{INK}">{code}</td></tr>'
            f'<tr><td align="center" style="padding:0 40px 4px;font-family:{SANS};font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:{INK}">Expires in {hours} hours</td></tr>'
            f'<tr><td align="center" style="padding:6px 60px 22px;font-family:{SANS};font-size:15px;line-height:1.6;color:{MUTED}">{html.escape(sub)}</td></tr>'
            f'<tr><td align="center" style="padding:0 40px 34px">{btn(cta, url, dark=True, pad="17px 34px")}</td></tr>')


def steps(items):
    """Zeitstrahl: Nummer, Titel, ein Satz."""
    rows = ""
    for i, it in enumerate(items, 1):
        k, _, v = it.partition(" — ")
        line = "" if i == len(items) else f'<div style="width:1px;height:46px;background:{RULE};margin:6px auto 0"></div>'
        rows += (f'<tr><td width="56" valign="top" align="center" style="padding:0"><div style="width:34px;height:34px;line-height:34px;border-radius:17px;background:{INK};color:#ffffff;font-family:{SANS};font-size:13px;text-align:center;margin:0 auto">{i}</div>{line}</td>'
                 f'<td valign="top" style="padding:4px 0 26px 10px"><div style="font-family:{SERIF};font-size:21px;line-height:1.2;color:{INK}">{html.escape(k)}</div>'
                 f'<div style="{BODY};font-size:14px;color:{MUTED};padding-top:4px">{html.escape(v)}</div></td></tr>')
    return f'<tr><td style="padding:30px 40px 10px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>'


def grid4(handles, label="", compare=True):
    """2 x 2, grosse Bilder, Name + Preis. compare=False: kein Streichpreis (wie products)."""
    cells = ""
    for i, hd in enumerate(handles[:4]):
        x = P[hd]; img = x["img"].split("?")[0] + "?width=600"
        cmp = f' <span style="text-decoration:line-through;opacity:.55">${x["compare"]:.0f}</span>' if compare and x.get("compare") else ""
        cells += (f'<td width="50%" valign="top" style="padding:{"0 5px 12px 0" if i % 2 == 0 else "0 0 12px 5px"}"><a href="{x["url"]}" style="text-decoration:none;color:{INK};display:block">'
                  f'<img src="{img}" width="290" alt="" style="display:block;width:100%;height:auto;background:{CARD}">'
                  f'<div style="font-family:{SERIF};font-size:16px;color:{INK};padding-top:10px">{html.escape(x["title"])}</div>'
                  f'<div style="font-family:{SANS};font-size:12px;letter-spacing:.06em;color:{MUTED};padding-top:3px">${x["price"]:.0f}{cmp}</div></a></td>')
        if i == 1: cells += "</tr><tr>"
    lab = f'<tr><td colspan="2" align="center" style="padding:0 0 18px;{EYE}">{html.escape(label)}</td></tr>' if label else ""
    return f'<tr><td style="padding:30px 28px 20px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{lab}<tr>{cells}</tr></table></td></tr>'


def build_one(m):
    url = m.get("url") or (SHOP + "/collections/all-products")
    if m.get("type") == "text":
        return plain(m)
    rows = head_row()
    if m.get("codebar"): rows += codebar(m["codebar"], m.get("codebar_url", url))
    style = m.get("hero_style", "full")
    if style == "text": rows += hero_text(m["headline"], m["sub"], m["cta1"], url, m.get("hero_eyebrow", ""), m.get("cta2"))
    elif style == "split": rows += hero_split(m["hero_image_kind"], m["headline"], m["sub"], m["cta1"], url, m.get("hero_eyebrow", ""), m.get("hero_code"))
    elif style == "type": rows += hero_type(m["big"], m["headline"], m["sub"], m["cta1"], url, m.get("hero_eyebrow", ""))
    else: rows += hero(m["hero_image_kind"], m["headline"], m["sub"], m["cta1"], url, m.get("hero_eyebrow", ""), m.get("cta2"), m.get("hero_h", 680))
    for b in m.get("blocks", []):
        t = b["type"]
        if t == "eyebrow": rows += eyebrow_row(b["text"])
        elif t == "headline": rows += headline_row(b["text"], b.get("size", 30))
        elif t == "text": rows += text_block(b["lines"], b.get("muted", False), b.get("pad", "6px 56px 30px"))
        elif t == "bullets": rows += bullets(b["items"], b.get("icons"))
        elif t == "statement": rows += statement(b["text"], b.get("pad", "10px 48px 26px"))
        elif t == "split": rows += split(b["kind"], b["headline"], b.get("text", ""), b.get("cta", "See more"), b.get("url", url), b.get("side", "left"), b.get("bg"), b.get("eyebrow", ""))
        elif t == "editorial": rows += editorial(b["kind"], b["text"], b.get("cta", "See more"), b.get("url", url), b.get("h", 640))
        elif t == "fade": rows += fade(b.get("a"), b.get("b"), b.get("h", 80))
        elif t == "band": rows += band(b["kind"], b.get("text", ""), b.get("cta"), b.get("url", url), b.get("h", 300), b.get("pos", "center 30%"))
        elif t == "strip": rows += strip(b["kinds"], b.get("h", 220), b.get("urls"))
        elif t == "tone": rows += tone(b["text"], b.get("sub", ""), b.get("bg"), b.get("dark", False), b.get("eyebrow", ""))
        elif t == "cartlist": rows += cartlist(b["handles"], b.get("cta", "Finish checkout"), b.get("url", url), b.get("label", "Your bag"))
        elif t == "kcart": rows += kcart(b.get("cta", "Finish checkout"), b.get("url", url), b.get("label", "Your bag"), b.get("source", "shopify"))
        elif t == "countdown": rows += countdown(b["head"], b["code"], b.get("sub", ""), b["cta"], b.get("url", url), b["hours"])
        elif t == "steps": rows += steps(b["items"])
        elif t == "grid4": rows += grid4(b["handles"], b.get("label", ""), b.get("compare", True))
        elif t == "image": rows += f'<tr><td style="padding:{b.get("pad", "0")}"><a href="{b.get("url", url)}"><img src="{img_for(b["kind"])}" width="600" alt="" style="display:block;width:100%;height:auto;background:{CARD}"></a></td></tr>'
        elif t == "list": rows += infolist(b["items"])
        elif t == "products": rows += products(b["handles"], b.get("label", ""), b.get("cta", ""), b.get("compare", True), b.get("dark", False))
        elif t == "facts": rows += facts(b["items"], b.get("icons"))
        elif t == "tile": rows += tile(b["image_kind"], b.get("label", ""), b["headline"], b["cta"], b["url"])
        elif t == "looks": rows += looks(b["items"], b.get("cta_all"), b.get("label", ""))
        elif t == "collections": rows += collections(b["items"], b.get("label", ""))
        elif t == "table": rows += table2(b["rows"], b.get("left", ""), b.get("right", ""))
        elif t == "proof" and b.get("text"): rows += proof(b["text"], b.get("who", ""))
        elif t == "reviews": rows += reviews(b["items"], b.get("label", ""))
        elif t == "code": rows += codeblock(b["head"], b["text"], b["code"], b["cta"], b["url"], b.get("note", ""), b.get("eyebrow", "Your first order"))
        elif t == "closing": rows += closing(b.get("image_kind", "room"), b["headline"], b["cta"], b.get("url", url), b.get("sub", ""))
        elif t == "spacer": rows += spacer(b.get("h", 18))
    rows += trustrow(m.get("trust")) + foot(m.get("footer_line", "Made, not photographed."))
    rows = re.sub(r"\{[%{].*?[%}]\}", lambda t: t.group(0).replace("&#x27;", "'").replace("&quot;", '"').replace("&amp;", "&"), rows)   # Klaviyo-Tags unescaped lassen
    pre = html.escape(m.get("preview", ""))
    return f"""<!doctype html><html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light only"><title>{html.escape(m['subject'])}</title>
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><style>td,p,a,span,div{{font-family:Georgia,serif!important}}</style><![endif]-->
<style>:root{{color-scheme:light only;supported-color-schemes:light only}} body{{margin:0;padding:0;background:{PAPER};mso-line-height-rule:exactly}} img{{border:0;-ms-interpolation-mode:bicubic}} table,td{{mso-table-lspace:0pt;mso-table-rspace:0pt}} a[x-apple-data-detectors]{{color:inherit!important;text-decoration:none!important}} @media only screen and (max-width:620px){{.col{{display:block!important;width:100%!important;box-sizing:border-box!important;padding:0 0 22px!important}} .hero{{height:auto!important}} .ov{{padding-top:250px!important}} .h1{{font-size:36px!important}} .h2{{font-size:32px!important}} .stk{{display:block!important}} .cta2{{padding:16px 0 0!important}} .f{{font-size:13px!important;white-space:nowrap}} .trust{{white-space:normal!important;padding:0 20px 22px!important}} .colp{{padding:26px 24px 30px!important}} .lk{{height:250px!important}} .lkov{{padding-top:186px!important}} .h3{{font-size:19px!important}} .scroll{{overflow-x:auto!important;-webkit-overflow-scrolling:touch;padding-bottom:18px}} .card{{width:210px!important}}}}</style></head>
<body style="margin:0;padding:0;background:{PAPER}"><div style="display:none;max-height:0;overflow:hidden;font-size:1px;color:{PAPER}">{pre}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER}"><tr><td align="center" style="padding:0 0 30px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:{WHITE};table-layout:fixed">{rows}</table></td></tr></table></body></html>"""


NO_PROOF = False
NOSEND = False                                # --nosend (17.09.): kein Telegram-Album je Mail beim Bauen (bei 20 Mails Spam)


def variant(m, v):
    """Mail m mit dem Einstieg der Variante v: subject/preview/headline/sub/hero_eyebrow/big; Textmails: erster Absatz nach „Hi,“ (text_open)."""
    mv = dict(m)
    for k in ("subject", "preview", "headline", "sub", "hero_eyebrow", "big", "hero_image_kind", "cta1", "hero_style"):   # Welle 2/3 (16.09.): Bild, Knopf, Layout
        if v.get(k): mv[k] = v[k]
    if v.get("blocks") is not None: mv["blocks"] = v["blocks"]   # 19.09.: Variante mit anderen Bloecken (Cross-Sell: A Code-Block, B ohne)
    if v.get("text_open") and mv.get("type") == "text":
        parts = mv["text"].split("\n\n"); parts[1] = v["text_open"]; mv["text"] = "\n\n".join(parts)
    return mv


def build(spec_path=None):
    spec = json.loads(pathlib.Path(spec_path or ROOT / "state/flows-spec.json").read_text())
    if NO_PROOF:
        for m in spec:
            m["blocks"] = [b for b in m.get("blocks", []) if b.get("type") not in ("proof", "reviews")]; m["placeholder_proof"] = False
    OUT.mkdir(parents=True, exist_ok=True); (OUT / "png").mkdir(exist_ok=True)
    for m in spec:
        if m.get("placeholder_proof"):
            print(f"  ! {m['flow']}: PLATZHALTER-Bewertungen/-Namen — vor Live-Gang durch echte ersetzen oder entfernen")
        html_src = build_one(m)                                     # build_one() ruft plain(m) selbst bei type "text"
        f = OUT / f"{m['flow']}.html"; f.write_text(html_src)
        for v in m.get("ab", []):                                   # A/B-Einstiege (16.09.): nur Betreff/Preheader/Hero anders, Rest gleich
            (OUT / f"{m['flow']}~{v['label']}.html").write_text(build_one(variant(m, v)))
        preview_src = preview_fill(html_src)
        assert not re.search(r"\{%|\{\{", preview_src), f"{m['flow']}: rohes Klaviyo-Tag in der Vorschau (sein Fund 20.09.)"
        prev = OUT / "png" / f"_preview-{m['flow']}.html"; prev.write_text(preview_src)
        r = subprocess.run([str(ROOT / ".venv/bin/python"), str(ROOT / "bin/shot.py"), prev.as_uri(), str(OUT / "png" / f"{m['flow']}.png"), "--w", "640", "--h", "900"],
                           capture_output=True, text=True)
        prev.unlink()
        print(m["flow"], "|", m["subject"], "|", (r.stdout or r.stderr).strip().splitlines()[-1][-40:])
        if m.get("type") == "text":
            continue
        inner = build_one(m).split('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#ffffff;table-layout:fixed"', 1)[1].split(">", 1)[1].rsplit("</table></td></tr></table></body></html>", 1)[0]
        sec = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:{WHITE};table-layout:fixed">{inner}</table>'
        (OUT / f"{m['flow']}-section.html").write_text(sec)
        assert len(sec.encode()) < 50_000, f"{m['flow']}: Section > 50 KB"


def snapshot():
    """state/products-email.json aus dem Shop erneuern (15.09.: stand seit 27 Produkten still; Hunter legt wöchentlich neue an)."""
    import importlib.util
    sp = importlib.util.spec_from_file_location("se", ROOT / "bin/shopify_edit.py"); se = importlib.util.module_from_spec(sp); sp.loader.exec_module(se)
    out, after = {}, None
    while True:
        d = se.gql("""query($c:String){ products(first:100, after:$c, query:"status:active"){ pageInfo{hasNextPage endCursor} nodes{ handle title descriptionHtml
              featuredMedia{ ... on MediaImage { image{ url } } } variants(first:1){ nodes{ price compareAtPrice } } } } }""", {"c": after})["products"]
        for n in d["nodes"]:
            v = n["variants"]["nodes"][0]
            out[n["handle"]] = {"title": n["title"], "url": f"https://nora-lanelle.com/products/{n['handle']}", "img": (n["featuredMedia"] or {}).get("image", {}).get("url", ""),
                                "price": float(v["price"]), "compare": float(v["compareAtPrice"]) if v["compareAtPrice"] else None,
                                "desc": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", n["descriptionHtml"] or "")).strip()}
        if not d["pageInfo"]["hasNextPage"]: break
        after = d["pageInfo"]["endCursor"]
    (ROOT / "state/products-email.json").write_text(json.dumps(out, indent=1, ensure_ascii=False)); print(len(out), "Produkte -> state/products-email.json")


def send(spec_path=None):
    spec = json.loads(pathlib.Path(spec_path or ROOT / "state/flows-spec.json").read_text())
    names = {"welcome": "Welcome", "cart": "Abandoned Cart", "checkout": "Abandoned Checkout", "browse": "Browse Abandonment", "post_purchase": "Post-Purchase", "winback": "Winback"}
    for m in spec:
        cap = (f"{names.get(m['flow'], m['flow'])} · Mail {m.get('email_no')} · {m['timing']}\nBetreff: {m['subject']}\nPreview: {m.get('preview','')}\n\nWarum so: {m.get('why','')}")
        if not NOSEND:
            subprocess.run([str(ROOT / ".venv/bin/python"), str(ROOT / "bin/tg-send-photos.py"), cap[:1000], str(OUT / "png" / f"{m['flow']}.png")])


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--klaviyo" in a:                      # Klaviyo-Import verlangt den Tag (Help 115005254068)
        UNSUB = "{% unsubscribe_link %}"; a.remove("--klaviyo")
    if "--nosend" in a:
        NOSEND = True; a.remove("--nosend")
    if "--no-proof" in a:                     # 15.09.: Platzhalter-Stimmen gehen nie nach Klaviyo (rules.md Social Proof) — Blöcke proof/reviews raus
        NO_PROOF = True; a.remove("--no-proof")
    if not a: print(__doc__); sys.exit(2)
    if a[0] == "snapshot": snapshot(); sys.exit(0)
    (build if a[0] == "build" else send)(a[1] if len(a) > 1 else None)
