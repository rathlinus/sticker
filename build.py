"""Builds index.html: every sticker from stickers.json on one page, each file inlined as a data URI.

    python build.py

The page needs no other file, so it works on GitHub Pages and opened straight from disk. Sizes come from
the SVGs: 10 SVG units = 1 mm unless the <svg> states its width in mm. Stickers that aren't SVG give
their size in stickers.json ("mm": [w, h]).
"""
import base64
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PX_PER_MM = 3.9
REPO = "https://github.com/rathlinus/sticker"


def size_mm(s):
    tag = s[s.index("<svg"):s.index(">", s.index("<svg"))]
    w, h = re.search(r'\swidth="([\d.]+)mm"', tag), re.search(r'\sheight="([\d.]+)mm"', tag)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    vb = [float(x) for x in re.search(r'viewBox="([^"]+)"', tag).group(1).replace(",", " ").split()]
    return vb[2] / 10, vb[3] / 10


def svg_uri(s):
    """Plain-text data URI. Only characters that would end or bend the URL get encoded, so it stays close
    to the file size; the page goes into a single-quoted attribute, so & and ' are escaped for HTML."""
    for a, b in (("%", "%25"), ("#", "%23"), ("\r", "%0D"), ("\n", "%0A"), ("\t", "%09")):
        s = s.replace(a, b)
    return "data:image/svg+xml;charset=utf-8," + s.replace("&", "&amp;").replace("'", "&#39;")


def sticker(it):
    path = HERE / it["file"]
    if path.suffix == ".svg":
        s = path.read_text(encoding="utf-8")
        w, h = size_mm(s)
        uri = svg_uri(s)
    else:
        w, h = it["mm"]
        mime = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg"}[path.suffix]
        uri = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
    c = html.escape(it["caption"])
    return (f'<figure class="st"><button type="button" class="zoom" data-file="{path.name}" data-cap="{c}" '
            f'data-mm="{w:.0f} × {h:.0f} mm" aria-label="{c} groß ansehen">'
            f"<img src='{uri}' alt=\"{c}\" width=\"{round(w * PX_PER_MM)}\" height=\"{round(h * PX_PER_MM)}\" "
            f'loading="lazy" decoding="async"></button><figcaption>{c}</figcaption></figure>')


HEAD = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Alle Sticker</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@700&family=Barlow:wght@400;500&display=swap">
<style>
  /* Header with an index of the sections, then one grey desk per section; stickers wrap at true size to each other (3.9 px per mm). One dark look on purpose, so white die-cut borders stay visible. */
  :root { --bg: #1a1a19; --desk: #4a4a46; --fg: #ececea; --muted: #a2a29a; --rule: #3a3a36; --focus: #f2c230;
    --head: 'Barlow Semi Condensed', 'Arial Narrow', sans-serif; --body: Barlow, system-ui, 'Segoe UI', sans-serif; color-scheme: dark; }
  body { margin: 0; background: var(--bg); color: var(--fg); font-family: var(--body); font-size: 16px; line-height: 1.5;
    padding-block: 32px 64px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
  main { display: grid; gap: 40px; }
  header { display: grid; gap: 12px; }
  h1, h2 { font-family: var(--head); font-weight: 700; margin: 0; text-wrap: balance; }
  h1 { font-size: 30px; line-height: 1.1; }
  h2 { font-size: 22px; line-height: 1.2; }
  p { margin: 0; color: var(--muted); max-width: 70ch; }
  a { color: var(--fg); text-underline-offset: 3px; }
  a:hover { text-decoration-color: var(--focus); }
  .n { color: var(--muted); font-family: var(--body); font-weight: 400; font-size: .8em; font-variant-numeric: tabular-nums; }
  nav { display: flex; flex-wrap: wrap; gap: 6px 20px; padding-top: 4px; border-top: 1px solid var(--rule); }
  section { display: grid; gap: 12px; min-width: 0; scroll-margin-top: 16px; }
  .sh { display: grid; gap: 2px; }
  .desk { background: var(--desk); border-radius: 8px; padding: clamp(12px, 3vw, 32px); display: flex; flex-wrap: wrap;
    gap: 20px 24px; align-items: flex-end; justify-content: center; }
  .st { margin: 0; display: flex; flex-direction: column; align-items: center; gap: 4px; max-width: 100%; min-width: 0; }
  .zoom { all: unset; display: block; cursor: zoom-in; max-width: 100%; border-radius: 4px; }
  .zoom:focus-visible { outline: 2px solid var(--focus); outline-offset: 4px; }
  .st img { display: block; height: auto; max-width: 100%; }
  figcaption { font-size: 12px; line-height: 1.3; color: var(--fg); opacity: .7; text-align: center; font-variant-numeric: tabular-nums; }
  dialog { border: 0; padding: 24px; background: var(--desk); color: var(--fg); border-radius: 8px; max-width: calc(100vw - 32px); box-sizing: border-box; }
  dialog::backdrop { background: rgb(0 0 0 / .75); }
  dialog img { display: block; margin: 0 auto; max-width: 100%; height: auto; }
  .dl { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 8px 16px; margin-top: 16px; }
  .dl p { color: var(--fg); }
  .dl span { color: var(--muted); }
  .acts { display: flex; gap: 16px; align-items: baseline; }
  #close { font: 500 15px/1 var(--body); color: var(--fg); background: var(--bg); border: 1px solid var(--muted); border-radius: 4px; padding: 8px 14px; cursor: pointer; }
  #close:hover { border-color: var(--fg); }
  #close:focus-visible, #save:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
</style>
</head>
<body>
"""

SCRIPT = """<script>
(() => {
  // Click a sticker to see it large; the file can be saved from there. The size in mm stays in the caption.
  const dlg = document.getElementById("big"), img = document.getElementById("bigimg"), save = document.getElementById("save");
  const cap = document.getElementById("bigcap"), mm = document.getElementById("bigmm");
  document.addEventListener("click", (e) => {
    const b = e.target.closest(".zoom");
    if (b) {
      const small = b.querySelector("img");
      const ratio = small.height / small.width;
      const w = Math.min(window.innerWidth - 80, 900, (window.innerHeight * 0.72) / ratio);
      img.src = small.src; img.alt = b.dataset.cap;
      img.style.width = Math.round(w) + "px";
      save.href = small.src; save.download = b.dataset.file;
      cap.textContent = b.dataset.cap; mm.textContent = b.dataset.mm;
      dlg.showModal();
      return;
    }
    if (e.target === dlg || e.target.id === "close") dlg.close();
  });
})();
</script>
</body>
</html>
"""

DIALOG = ('<dialog id="big"><img id="bigimg" alt=""><div class="dl"><p><span id="bigcap"></span> '
          '<span id="bigmm"></span></p><div class="acts"><a id="save" href="#">Datei speichern</a>'
          '<button type="button" id="close">Schließen</button></div></div></dialog>')


def main():
    data = json.loads((HERE / "stickers.json").read_text(encoding="utf-8"))
    nav, body = [], []
    total = 0
    for sec in data["sections"]:
        n = len(sec["stickers"])
        total += n
        nav.append(f'<a href="#{sec["id"]}">{html.escape(sec["title"])} <span class="n">{n}</span></a>')
        body.append(f'<section id="{sec["id"]}"><div class="sh"><h2>{html.escape(sec["title"])} <span class="n">{n}</span></h2>'
                    f'<p>{sec["note"]}</p></div><div class="desk">{"".join(sticker(it) for it in sec["stickers"])}</div></section>')
    intro = (f'{total} Sticker in echter Größe zueinander, Stand {data["date"]}. Ein Klick zeigt einen Sticker groß. '
             f'Alle Dateien liegen einzeln im <a href="{REPO}">Repo</a>.')
    main_ = (f'<main><header><h1>{html.escape(data["title"])}</h1><p>{intro}</p><nav>{"".join(nav)}</nav></header>'
             f'{"".join(body)}</main>{DIALOG}')
    out = HERE / "index.html"
    out.write_text(HEAD + main_ + "\n" + SCRIPT, encoding="utf-8", newline="\n")
    print(f"{total} stickers, index.html {out.stat().st_size / 2**20:.1f} MB")


if __name__ == "__main__":
    main()
