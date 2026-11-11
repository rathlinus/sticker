"""Builds index.html: every sticker from stickers.json on one sheet, in the order the file lists them,
each file inlined as a data URI.

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
    return (f'<button type="button" class="zoom" data-file="{path.name}" data-cap="{c}" '
            f'data-mm="{w:.0f} × {h:.0f} mm" aria-label="{c} groß ansehen">'
            f"<img src='{uri}' alt=\"{c}\" width=\"{round(w * PX_PER_MM)}\" height=\"{round(h * PX_PER_MM)}\" "
            f'loading="lazy" decoding="async"></button>')


HEAD = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Alle Sticker</title>
<style>
  /* One grey sheet with every sticker at true size to each other (3.9 px per mm). One dark look on purpose, so white die-cut borders stay visible. */
  :root { --bg: #1a1a19; --desk: #4a4a46; --fg: #ececea; --muted: #a2a29a; --focus: #f2c230; color-scheme: dark; }
  body { margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.5 system-ui, 'Segoe UI', sans-serif;
    padding: 16px max(16px, env(safe-area-inset-right, 0px)) 16px max(16px, env(safe-area-inset-left, 0px)); }
  main { background: var(--desk); border-radius: 8px; padding: clamp(12px, 3vw, 32px); display: flex; flex-wrap: wrap;
    gap: 16px 20px; align-items: center; justify-content: center; }
  .zoom { all: unset; display: block; cursor: zoom-in; max-width: 100%; border-radius: 4px; }
  .zoom:focus-visible { outline: 2px solid var(--focus); outline-offset: 4px; }
  .zoom img { display: block; height: auto; max-width: 100%; }
  main.packed { display: block; position: relative; }
  .packed .zoom { position: absolute; }
  .packed .zoom img { width: 100%; }
  dialog { border: 0; padding: 24px; background: var(--desk); color: var(--fg); border-radius: 8px; max-width: calc(100vw - 32px); box-sizing: border-box; }
  dialog::backdrop { background: rgb(0 0 0 / .75); }
  dialog img { display: block; margin: 0 auto; max-width: 100%; height: auto; }
  .dl { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 8px 16px; margin-top: 16px; }
  .dl p { margin: 0; }
  .dl span + span { color: var(--muted); }
  .acts { display: flex; gap: 16px; align-items: baseline; }
  a { color: var(--fg); text-underline-offset: 3px; }
  a:hover { text-decoration-color: var(--focus); }
  #close { font: 500 15px/1 system-ui, 'Segoe UI', sans-serif; color: var(--fg); background: var(--bg); border: 1px solid var(--muted); border-radius: 4px; padding: 8px 14px; cursor: pointer; }
  #close:hover { border-color: var(--fg); }
  #close:focus-visible, #save:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
</style>
</head>
<body>
"""

SCRIPT = """<script>
(() => {
  // Nest the stickers like a printed sheet: in list order, each goes to the highest free spot (skyline packing
  // of the bounding boxes), then the whole block is centred. Stickers wider than the sheet shrink to fit.
  const sheet = document.querySelector("main"), G = 16;
  const items = [...sheet.querySelectorAll(".zoom")].map((b) => {
    const i = b.querySelector("img");
    return { b, w: +i.getAttribute("width"), h: +i.getAttribute("height") };
  });
  let lastW = 0;
  function pack() {
    const cs = getComputedStyle(sheet);
    const W = sheet.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    if (Math.abs(W - lastW) < 1) return;
    lastW = W;
    let sky = [{ x: 0, y: 0, w: W }], right = 0, bottom = 0;
    const pos = items.map((it) => {
      const s = Math.min(1, W / it.w), w = it.w * s, h = it.h * s;
      let best = null;
      for (let i = 0; i < sky.length; i++) {
        const x = sky[i].x;
        if (x + w > W + 0.5) break;
        let y = 0;
        for (let j = i; j < sky.length && sky[j].x < x + w; j++) y = Math.max(y, sky[j].y);
        if (!best || y < best.y) best = { x, y };
      }
      const { x, y } = best, x2 = x + w + G, next = [];
      for (const seg of sky) {
        const end = seg.x + seg.w;
        if (end <= x || seg.x >= x2) next.push(seg);
        else {
          if (seg.x < x) next.push({ x: seg.x, y: seg.y, w: x - seg.x });
          if (end > x2) next.push({ x: x2, y: seg.y, w: end - x2 });
        }
      }
      next.push({ x, y: y + h + G, w: x2 - x });
      next.sort((a, b) => a.x - b.x);
      sky = [];
      for (const seg of next) {
        const l = sky[sky.length - 1];
        if (l && l.y === seg.y && Math.abs(l.x + l.w - seg.x) < 0.01) l.w += seg.w;
        else sky.push({ ...seg });
      }
      right = Math.max(right, x + w);
      bottom = Math.max(bottom, y + h);
      return { x, y, w };
    });
    // absolute positions start at the padding edge, so add the padding back in
    const left = parseFloat(cs.paddingLeft) + (W - right) / 2, top = parseFloat(cs.paddingTop);
    items.forEach((it, k) => {
      it.b.style.left = left + pos[k].x + "px";
      it.b.style.top = top + pos[k].y + "px";
      it.b.style.width = pos[k].w + "px";
    });
    sheet.style.height = bottom + "px";
    sheet.classList.add("packed");
  }
  pack();
  new ResizeObserver(pack).observe(sheet);

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
    stickers = data["stickers"]
    page = f'<main>{"".join(sticker(it) for it in stickers)}</main>{DIALOG}'
    out = HERE / "index.html"
    out.write_text(HEAD + page + "\n" + SCRIPT, encoding="utf-8", newline="\n")
    print(f"{len(stickers)} stickers, index.html {out.stat().st_size / 2**20:.1f} MB")


if __name__ == "__main__":
    main()
