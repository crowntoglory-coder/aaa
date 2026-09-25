# E-Mail-Gestaltung — was bei teuren Marken funktioniert

Recherchiert 09.09.2026. Vorbereitung auf die Vorlagen, die er schickt. Quellen unten.

---

## Die drei Fallen, die teure E-Mails billig aussehen lassen

**1. Die Überschrift steckt im Bild.**
Verschwindet die Kopfzeile, wenn Bilder blockiert sind, ist die Mail kaputt. Outlook blockiert
standardmäßig, viele Leute auch. Ein Vollbild-Hero mit eingebautem „NEW IN" ist bei blockierten
Bildern eine leere Fläche.
→ **Echter Text über dem Bild**, nicht im Bild. Genau wie beim Hero auf der Startseite: Bild
als Hintergrund, Schrift als HTML darüber. Was ins Bild muss, bekommt Alt-Text.

**2. Dunkelmodus dreht Farben, aber nicht überall gleich.**
Drei verschiedene Probleme: Apple Mail invertiert aggressiv, Outlook (Desktop) fast gar nicht,
Gmail invertiert nur Teile der Palette. Ein cremefarbener Grund wird bei Apple dunkelbraun, das
schwarze Logo darauf verschwindet.
→ `@media (prefers-color-scheme: dark)` mit eigenen Farben. Logos und Knöpfe so bauen, dass sie
eine Invertierung überleben (PNG mit transparentem Grund, nicht weiß auf weiß). Vorher in
echten Konten testen, nicht nur in der Vorschau.

**3. Gmail schneidet ab 102 KB ab.**
Alles darunter fällt weg — inklusive Abmeldelink und Zählpixel. Das kostet Zustellbarkeit und
ist ein rechtliches Problem, weil der Abmeldelink pflicht ist.
→ Kein Inline-CSS-Wust, keine base64-Bilder, keine Kommentare im Code. Vor dem Versand die
Größe messen.

---

## Aufbau, den teure Modemarken benutzen

    Kopf        Logo mittig, darunter höchstens 4 Links. Keine volle Navigation.
    Hero        vollflächiges Bild, Text als HTML darüber, EIN Aufruf
    Aufmacher   2–3 Sätze, die den Aufruf vorbereiten — nicht der Aufruf allein
    Produkte    2 Spalten mobil, nie mehr. Bild, Name, Preis, sonst nichts.
    Zweiter Aufruf
    Fuß         Zusagen, Kontakt, Abmeldung

**Die Regel dahinter:** Wer erfolgreich ist, wirft den Knopf nicht ans Ende. Er baut ihn mit
zwei, drei Sätzen auf, die den Klick verdienen. Ein Knopf ohne Vorlauf ist eine Aufforderung
ohne Grund.

**Mischung:** rund 60 % Inspiration und Stil, 40 % Verkauf. Wer 100 % verkauft, wird
weggewischt; wer 100 % inspiriert, verkauft nichts.

---

## Maße, die stimmen müssen

    Breite            600 px, eine Spalte. Zwei Spalten nur für Produktkacheln.
    Hero-Bild         1200 px breit (für Retina), unter 200 KB
    Gesamtgewicht     unter 102 KB HTML, Bilder extern
    Knopf             mindestens 44 px hoch — Fingergröße, keine Design-Frage
    Kontrast          4,5:1 für Text, sonst filtern Gmail und Apple mit
    Alt-Text          auf jedem Bild. Zählt 2026 in die Spamfilter mit ein.

Über 70 % der Modemails werden auf dem Handy geöffnet. Das heißt: eine Spalte, große Schrift,
große Tippziele — und der Entwurf beginnt beim Handy, nicht beim Desktop.

---

## Übertragen auf Nora Lanelle

Die Marke hat einen Vorteil, den die meisten nicht haben: eine **eigene Bildsprache**. Die vier
Kampagnenbilder (Straße im Streiflicht, Raum mit Lichtschneise, Terrasse zur blauen Stunde,
zwei Figuren an der Wand) sind genau das Material, aus dem sich Hero-Bilder schneiden lassen.

    Hero          campaign-hero*.jpg, 16:9 auf 1200 px beschnitten
    Schrift       Versal, weit gesperrt, weiß auf dem dunklen Teil des Bildes
    Aufruf        unterstrichen, kein Kasten — wie auf der Website
    Palette hell  #f4f4f5 Grund, #2a2320 Text
    Palette dunkel #1c1815 Grund, #f2efe9 Text

**Was NICHT hineindarf**, weil die About-Seite es ausschließt: Countdown, „nur noch X Stück",
„12 andere sehen das gerade", erfundene Bewertungen. Und wo ein gestyltes Bild vorkommt, gehört
der Hinweis dazu, dass es gemacht und nicht fotografiert ist.

---

## Vor jedem Versand prüfen

    ☐ Überschrift sichtbar, wenn Bilder blockiert sind
    ☐ Im Dunkelmodus gelesen — Apple Mail UND Gmail
    ☐ HTML unter 102 KB
    ☐ Alt-Text auf jedem Bild
    ☐ Knöpfe mindestens 44 px
    ☐ An echte Konten getestet, nicht nur in der Vorschau
    ☐ Abmeldelink sichtbar
    ☐ SPF, DKIM und DMARC stehen

---

## Quellen

Litmus (Dunkelmodus) · emfluence (Barrierefreiheit 2026) · Moosend (Modemarken-Beispiele) ·
Mail Designer 365 · Digital Applied (Maße 2026)
