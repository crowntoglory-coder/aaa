# Cloud-Start — E-Mail-Agenten-Modus (25.09.)

Einfügen in die Cloud-Sitzung (claude.ai/code, Repo crowntoglory-coder/aaa):

> Lies CLOUD-START.md und arbeite den Auftrag ab. Ergebnis als Pull Request.

## Kontext
Dieses Repo ist ein Stand ohne Schlüssel (.env/*.key fehlen) und ohne Git-Historie. Klaviyo/Shopify/Meta sind von hier
NICHT erreichbar — nichts live schalten, nur Dateien ändern. Die lokale Sitzung schaltet den PR danach live
(`flows.py snapshot` → `flows.py build --klaviyo --no-proof <spec>` für alle `klaviyo.SPECS` → `klaviyo.py recreate`).
Lesen: CLAUDE.md, HANDOVER.md §0 (24.09.), marketing/CONTEXT.md, _client-context/rules.md (Einträge 24./25.09.),
_reference/psychologie.md §8, _reference/email-cro.md §7, _reference/funnel.md §2, _reference/email-design.md.
Mail-Texte: state/flows-*.json (Reihenfolge = `SPECS` in bin/klaviyo.py, spätere Spec gewinnt). Flow-Aufbau: `PLAN` in bin/klaviyo.py.

## Auftrag (seine Worte 24./25.09., alles umsetzen)
1. **Tabelle** (`marketing/workflows/04-output/2026-09-25-mail-matrix.md`): je Kundinnen-Typ — nur Anmeldung · Produkt angesehen ·
   Warenkorb · nur Checkout · Kauf (inkl. Bestellmails danach) · Wiederkauf · inaktiv — wie viele Mails, wann, welche; Summen;
   ehrliches Urteil, wie gut das ist (zu viel/zu wenig, Lücken, Doppel).
2. **Neue A/B-Tests** statt der 42 blockierten (Klaviyo startet Tests auf Mails mit `additional_filters` per API nicht — Lösung
   vorschlagen und im PLAN umsetzen): Betreff-Hooks dringlicher; Vorschautext OHNE Rabattcode (Code wirkt „salesly“);
   Absendername „NORA-LANELLE“ gegen „Nora Lanelle“. Je Test 1 Variable.
3. **Ganzer Funnel mit frischem Wissen** (lange, gründlich): Timing, Reihenfolge, Angebot, Kappe, Browse/Cart ohne identifizierte
   Besucherinnen (Popup meldet nur bei Shopify an → Klaviyo `identify` fehlt), Zustellbarkeit (Sending Domain, DMARC), was fehlt.
   Jede Änderung mit Begründung + Quelle im PR-Text.
4. Preise sind seit 24.09. −20 % (bin/reprice.py) — Texte dürfen keine alten Preise nennen; Preise kommen aus state/products-email.json.
5. Regeln: keine erfundenen Stimmen/Zahlen, „easy returns“, Versand frei ab $150, WELCOME15 = 15 % (Wert nie ändern).

Autumn Special (alle Produkte rein, Kleidung vorn) und das Löschen der Flow-Entwürfe macht die lokale Sitzung — braucht die Schlüssel.
