# Sticker

Alle 235 Sticker, Stand 9. November 2026, auf einem Bogen in echter Größe zueinander: https://rathlinus.github.io/sticker/

- svg/: ein SVG pro Sticker, ohne Beschnitt und Schnittlinie. Wo die Datei keine Größe in mm angibt, sind 10 Einheiten 1 mm.
- holo-02.webp: Vorschau von Sticker 2 auf Holofolie.
- stickers.json: alle Sticker in der Reihenfolge auf dem Bogen (einmal zufällig gemischt), mit Beschriftung und der Gruppe, aus der sie stammen.
- index.html: der Bogen als eine einzige Datei, alle Sticker darin eingebettet.

Nach Änderungen an svg/ oder stickers.json den Bogen neu bauen:

```
python build.py
```
