"""Build semantic, PDF-faithful web pages 6-72.

The legacy conversion contains exact word positions over a rendered PDF page.
This script turns those positions into visible HTML and produces a text-free
art layer from each render.  It is intentionally idempotent: source extraction
is always performed from the legacy page-render plus the original HTML word
map, while already-converted pages are skipped unless their cached source map
exists in ``tools/source-maps``.
"""

from __future__ import annotations

import html
import json
import math
import re
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ART_DIR = ROOT / "images" / "semantic-art"
MAP_DIR = ROOT / "tools" / "source-maps"
PAGE_WIDTH = 900
PAGE_HEIGHT = 1239

WORD_RE = re.compile(
    r'<span class="pdf-word"[^>]*data-word-index="(?P<index>\d+)"[^>]*'
    r'style="left:(?P<left>[\d.]+)%;top:(?P<top>[\d.]+)%;'
    r'width:(?P<width>[\d.]+)%;height:(?P<height>[\d.]+)%">'
    r'(?P<text>.*?)</span>',
    re.S,
)
TRANSCRIPT_RE = re.compile(
    r'<span data-id="(?P<id>[^"]+)">(?P<text>.*?)</span>', re.S
)


def repair_text(value: str) -> str:
    return (
        value.replace("â€™", "’")
        .replace("â€“", "–")
        .replace("Ã—", "×")
        .replace("\ufffd", "")
    )


def page_path(page: int) -> Path:
    return ROOT / ("index.html" if page == 1 else f"pg{page:03d}_sec001.html")


def parse_legacy(page: int) -> tuple[list[dict], list[dict]]:
    cache = MAP_DIR / f"pg{page:03d}.json"
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        changed = False
        for collection in (data["words"], data["transcript"]):
            for item in collection:
                fixed = repair_text(item["text"])
                if fixed != item["text"]:
                    item["text"] = fixed
                    changed = True
        if changed:
            cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data["words"], data["transcript"]

    source = page_path(page).read_text(encoding="utf-8")
    words = []
    for match in WORD_RE.finditer(source):
        item = match.groupdict()
        words.append(
            {
                "index": int(item["index"]),
                "left": float(item["left"]),
                "top": float(item["top"]),
                "width": float(item["width"]),
                "height": float(item["height"]),
                "text": repair_text(html.unescape(re.sub(r"<[^>]+>", "", item["text"]))),
            }
        )
    transcript = [
        {
            "id": match.group("id"),
            "text": repair_text(html.unescape(re.sub(r"<[^>]+>", "", match.group("text")))),
        }
        for match in TRANSCRIPT_RE.finditer(source)
    ]
    if not words:
        raise RuntimeError(f"No legacy word map found for page {page}")
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"words": words, "transcript": transcript}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return words, transcript


def is_production_word(word: dict) -> bool:
    text = word["text"].strip()
    if word["top"] >= 96.0:
        return True
    if 90.0 <= word["top"] <= 95.5 and 40.0 <= word["left"] <= 60.0:
        return bool(re.fullmatch(r"(?:\d+|[ivxlcdm]+)", text, re.I))
    return False


def clean_transcript(items: list[dict]) -> list[dict]:
    cleaned = []
    total = len(items)
    for pos, item in enumerate(items):
        text = " ".join(item["text"].split())
        if not text:
            continue
        if re.search(r"\.indd\b|\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}", text, re.I):
            continue
        if pos >= total - 3 and re.fullmatch(r"(?:\d+|[ivxlcdm]+)", text, re.I):
            continue
        cleaned.append({"id": item["id"], "text": text})
    return cleaned


def art_alt(page: int, transcript: list[dict]) -> str:
    if page == 6:
        return ""
    if page == 69:
        return (
            "Hatua za huduma ya kwanza: kufunga jeraha, kunawa mikono, "
            "na kumpeleka aliyeumia zahanati."
        )
    text = " ".join(item["text"] for item in clean_transcript(transcript)[:2])
    words = text.split()
    if len(words) > 18:
        text = " ".join(words[:18]) + "…"
    return "Michoro na vielelezo vya " + text.rstrip(".:") + "."


def pct_box(word: dict, image: Image.Image) -> tuple[int, int, int, int]:
    width, height = image.size
    left = int(round(word["left"] * width / 100))
    top = int(round(word["top"] * height / 100))
    right = int(round((word["left"] + word["width"]) * width / 100))
    bottom = int(round((word["top"] + word["height"]) * height / 100))
    return left, top, right, bottom


def quantized_colour(colour: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(min(255, int(round(channel / 16) * 16)) for channel in colour)


def sample_colours(image: Image.Image, box: tuple[int, int, int, int]) -> tuple[str, tuple[int, int, int]]:
    """Return a likely foreground CSS colour and a local background colour."""
    left, top, right, bottom = box
    width, height = image.size
    pad = max(3, int(round((bottom - top) * 0.35)))
    outer = (
        max(0, left - pad),
        max(0, top - pad),
        min(width, right + pad),
        min(height, bottom + pad),
    )
    pixels = image.load()
    ring = []
    for y in range(outer[1], outer[3]):
        for x in range(outer[0], outer[2]):
            if left <= x < right and top <= y < bottom:
                continue
            ring.append(pixels[x, y][:3])
    if ring:
        qr = Counter(quantized_colour(pixel) for pixel in ring)
        background = qr.most_common(1)[0][0]
    else:
        background = (255, 255, 255)

    inside = []
    for y in range(max(0, top), min(height, bottom)):
        for x in range(max(0, left), min(width, right)):
            colour = pixels[x, y][:3]
            distance = math.sqrt(sum((colour[i] - background[i]) ** 2 for i in range(3)))
            if distance >= 48:
                inside.append(colour)
    if not inside:
        foreground = (45, 45, 45)
    else:
        candidates = Counter(quantized_colour(pixel) for pixel in inside)
        bg_luma = sum(background) / 3
        ranked = []
        for colour, count in candidates.items():
            distance = math.sqrt(sum((colour[i] - background[i]) ** 2 for i in range(3)))
            luma = sum(colour) / 3
            contrast_bonus = (luma - bg_luma) if bg_luma < 145 else (bg_luma - luma)
            ranked.append((count * (1 + distance / 180) + max(0, contrast_bonus), colour))
        foreground = max(ranked)[1]
    return "#{:02x}{:02x}{:02x}".format(*foreground), background


def build_art(page: int, words: list[dict]) -> dict[int, str]:
    source = ROOT / "images" / "page-renders" / f"pg{page:03d}.png"
    image = Image.open(source).convert("RGB")
    colours: dict[int, str] = {}
    backgrounds: dict[int, tuple[int, int, int]] = {}
    boxes: dict[int, tuple[int, int, int, int]] = {}
    for word in words:
        box = pct_box(word, image)
        colour, background = sample_colours(image, box)
        colours[word["index"]] = colour
        backgrounds[word["index"]] = background
        boxes[word["index"]] = box

    draw = ImageDraw.Draw(image)
    # Remove crop/registration marks and printer metadata outside the page frame.
    draw.rectangle((0, 0, image.width, 37), fill=(255, 255, 255))
    draw.rectangle((0, 0, 34, image.height), fill=(255, 255, 255))
    draw.rectangle((image.width - 35, 0, image.width, image.height), fill=(255, 255, 255))
    draw.rectangle((0, 1200, image.width, image.height), fill=(255, 255, 255))

    for word in words:
        box = boxes[word["index"]]
        left, top, right, bottom = box
        if is_production_word(word) and 90 <= word["top"] < 96:
            # Printed folios sit on a blue pill with a shadow; remove the whole pill.
            left, right = max(0, left - 38), min(image.width, right + 38)
            top, bottom = max(0, top - 18), min(image.height, bottom + 22)
            fill = (255, 255, 255)
        else:
            expand = max(1, int(round((bottom - top) * 0.08)))
            left, top = max(0, left - expand), max(0, top - expand)
            right, bottom = min(image.width, right + expand), min(image.height, bottom + expand)
            fill = backgrounds[word["index"]]
        draw.rectangle((left, top, right, bottom), fill=fill)

    remove_blue_border(image)

    ART_DIR.mkdir(parents=True, exist_ok=True)
    output = ART_DIR / f"pg{page:03d}-art.png"
    image.save(output, optimize=True)
    return colours


def remove_blue_border(image: Image.Image) -> None:
    """Remove the pale cyan printed-page gradient without touching artwork."""
    pixels = image.load()
    width, height = image.size
    for y in list(range(102)) + list(range(height - 102, height)):
        for x in range(width):
            red, green, blue = pixels[x, y][:3]
            if red > 205 and green > 208 and blue > 212 and blue - red > 3 and green - red > 2:
                pixels[x, y] = (255, 255, 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 111, height), fill=(255, 255, 255))
    draw.rectangle((width - 112, 0, width, height), fill=(255, 255, 255))
    draw.rectangle((0, 0, width, 41), fill=(255, 255, 255))
    draw.rectangle((0, height - 42, width, height), fill=(255, 255, 255))


def group_lines(words: list[dict]) -> list[list[dict]]:
    ordered = sorted(words, key=lambda item: (item["top"], item["left"]))
    lines: list[list[dict]] = []
    for word in ordered:
        target = None
        for line in reversed(lines[-4:]):
            line_top = sum(item["top"] for item in line) / len(line)
            tolerance = max(0.22, min(word["height"], max(item["height"] for item in line)) * 0.28)
            if abs(word["top"] - line_top) <= tolerance:
                target = line
                break
        if target is None:
            lines.append([word])
        else:
            target.append(word)
    for line in lines:
        line.sort(key=lambda item: item["left"])
    return lines


def line_tag(line: list[dict]) -> str:
    text = " ".join(item["text"] for item in line).strip()
    max_height = max(item["height"] for item in line)
    if re.match(r"^Sura\s+ya\b", text, re.I) or max_height >= 4.0:
        return "h2"
    if re.match(r"^(?:Utangulizi|Zoezi\s+la|Kazi\s+ya|Mada\b)", text, re.I) or max_height >= 2.75:
        return "h3"
    return "p"


def render_word(word: dict, colour: str, output_index: int) -> str:
    size = max(0.82, word["height"] * 1.12)
    weight = 700 if word["height"] >= 2.45 else 400
    safe = html.escape(word["text"])
    style = (
        f"left:{word['left']:.4f}%;top:{word['top']:.4f}%;"
        f"width:{word['width']:.4f}%;height:{word['height']:.4f}%;"
        f"font-size:{size:.3f}cqw;color:{colour};font-weight:{weight}"
    )
    return (
        f'<span class="pdf-word semantic-word semantic-positioned-word" '
        f'data-word-index="{output_index}" style="{style}">{safe} </span>'
    )


def build_page(page: int, words: list[dict], transcript: list[dict], colours: dict[int, str]) -> None:
    content_words = [word for word in words if not is_production_word(word)]
    lines = group_lines(content_words)
    output_index = 0
    groups = []
    for line_no, line in enumerate(lines, 1):
        tag = line_tag(line)
        rendered = []
        for word in line:
            rendered.append(render_word(word, colours[word["index"]], output_index))
            output_index += 1
        groups.append(
            f'        <{tag} class="semantic-text-group" data-line="{line_no}">'
            + "".join(rendered)
            + f"</{tag}>"
        )

    narration = clean_transcript(transcript)
    hook = ""
    if narration:
        spans = " ".join(
            f'<span data-id="{html.escape(item["id"], quote=True)}">{html.escape(item["text"])}</span>'
            for item in narration
        )
        hook = (
            '      <div class="page-narration-hook accessible-transcript sr-only" '
            f'aria-label="Maandishi ya ukurasa">{spans}</div>\n'
        )

    body = "\n".join(groups)
    label = f"Ukurasa {page} wa kitabu"
    title = f"Afya na Mazingira - Mwaka wa Kwanza - Ukurasa {page}"
    illustration_alt = art_alt(page, transcript)
    art_accessibility = (
        f'alt="{html.escape(illustration_alt, quote=True)}"'
        if illustration_alt
        else 'alt="" aria-hidden="true"'
    )
    document = f'''<!doctype html>
<html lang="sw-TZ">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="title-id" content="pg{page:03d}_sec001">
  <meta name="page-section-id" content="{page}">
  <title>{title}</title>
  <link href="./content/tailwind_output.css" rel="stylesheet">
  <link href="./assets/libs/fontawesome/css/all.min.css" rel="stylesheet">
  <link href="./assets/fonts.css" rel="stylesheet">
  <link rel="stylesheet" href="./assets/reader.css?v=semantic26">
</head>
<body>
  <main>
    <h1 class="sr-only">Afya na Mazingira, ukurasa {page}</h1>
    <article class="semantic-page semantic-generated-page page-shell" aria-label="{label}">
      <img class="semantic-art-layer" src="images/semantic-art/pg{page:03d}-art.png" {art_accessibility}>
      <section class="page-inner positioned-semantic-content" aria-label="Maudhui ya ukurasa">
{body}
      </section>
{hook}    </article>
  </main>
  <div class="relative z-50" id="interface-container"></div>
  <div class="relative z-50" id="nav-container"></div>
  <script src="./assets/scorm.js"></script>
  <script src="./assets/pdf-word-highlight.js?v=20260828-semantic2"></script>
  <script src="./assets/sign-language-video-muted.js?v=1"></script>
  <script src="./assets/audio-speed-default.js?v=1"></script>
  <script src="./assets/base.bundle.local.js?v=audio085"></script>
  <script src="./content/exercises.js?v=8"></script>
  <script src="./assets/exercise-interactions.js?v=20"></script>
</body>
</html>
'''
    page_path(page).write_text(document, encoding="utf-8")


def main() -> None:
    report = []
    border_marker = ART_DIR / ".borderless-v2"
    border_cleanup_needed = not border_marker.exists()
    for page in range(6, 73):
        existing_page = page_path(page)
        existing_art = ART_DIR / f"pg{page:03d}-art.png"
        if (
            existing_art.exists()
            and existing_page.exists()
            and "semantic-generated-page" in existing_page.read_text(encoding="utf-8")
        ):
            words, transcript = parse_legacy(page)
            report.append(
                {
                    "page": page,
                    "source_words": len(words),
                    "html_words": sum(not is_production_word(word) for word in words),
                    "narration_segments": len(clean_transcript(transcript)),
                }
            )
            continue
        words, transcript = parse_legacy(page)
        colours = build_art(page, words)
        build_page(page, words, transcript, colours)
        report.append(
            {
                "page": page,
                "source_words": len(words),
                "html_words": sum(not is_production_word(word) for word in words),
                "narration_segments": len(clean_transcript(transcript)),
            }
        )
    (ROOT / "tools" / "semantic-build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Keep the existing accessibility narration enhancements, but the runtime
    # now suppresses their old visual screenshot patches on semantic pages.
    for page in range(6, 73):
        target = page_path(page)
        source = target.read_text(encoding="utf-8")
        source = repair_text(source)
        source = source.replace("reader.css?v=semantic2", "reader.css?v=semantic4")
        source = source.replace("reader.css?v=semantic3", "reader.css?v=semantic4")
        source = source.replace("reader.css?v=semantic4", "reader.css?v=semantic5")
        source = source.replace("reader.css?v=semantic5", "reader.css?v=semantic6")
        source = source.replace("reader.css?v=semantic6", "reader.css?v=semantic7")
        source = source.replace("reader.css?v=semantic7", "reader.css?v=semantic8")
        source = source.replace("reader.css?v=semantic8", "reader.css?v=semantic9")
        source = source.replace("reader.css?v=semantic9", "reader.css?v=semantic10")
        source = source.replace("reader.css?v=semantic10", "reader.css?v=semantic11")
        source = source.replace("reader.css?v=semantic11", "reader.css?v=semantic12")
        source = source.replace("reader.css?v=semantic12", "reader.css?v=semantic13")
        source = source.replace("reader.css?v=semantic13", "reader.css?v=semantic14")
        source = source.replace("reader.css?v=semantic14", "reader.css?v=semantic15")
        source = source.replace("reader.css?v=semantic15", "reader.css?v=semantic16")
        source = source.replace("reader.css?v=semantic16", "reader.css?v=semantic17")
        source = source.replace("reader.css?v=semantic17", "reader.css?v=semantic18")
        source = source.replace("reader.css?v=semantic18", "reader.css?v=semantic19")
        source = source.replace("reader.css?v=semantic19", "reader.css?v=semantic20")
        source = source.replace("reader.css?v=semantic20", "reader.css?v=semantic21")
        source = source.replace("reader.css?v=semantic21", "reader.css?v=semantic22")
        source = source.replace("reader.css?v=semantic22", "reader.css?v=semantic23")
        source = source.replace("reader.css?v=semantic23", "reader.css?v=semantic24")
        source = source.replace("reader.css?v=semantic24", "reader.css?v=semantic25")
        source = source.replace("reader.css?v=semantic25", "reader.css?v=semantic26")
        if page == 69 and "page-narration-hook" not in source:
            words, transcript = parse_legacy(page)
            anchor = transcript[0]
            hook = (
                '      <div class="page-narration-hook accessible-transcript sr-only" '
                'aria-label="Maelezo ya michoro ya ukurasa">'
                f'<span data-id="{html.escape(anchor["id"], quote=True)}">'
                f'{html.escape(anchor["text"])}</span></div>\n'
            )
            source = source.replace("    </article>\n", hook + "    </article>\n")
        words, transcript = parse_legacy(page)
        illustration_alt = art_alt(page, transcript)
        art_accessibility = (
            f'alt="{html.escape(illustration_alt, quote=True)}"'
            if illustration_alt
            else 'alt="" aria-hidden="true"'
        )
        source = re.sub(
            r'(<img class="semantic-art-layer"[^>]*?)\s+alt="[^"]*"(?:\s+aria-hidden="true")?\s*>',
            lambda match: re.sub(r'\s+$', '', match.group(1)) + " " + art_accessibility + ">",
            source,
            count=1,
        )
        if "validator-enhancements.js" not in source:
            source = source.replace(
                "</body>",
                '  <script src="./assets/validator-enhancements.js?v=semantic2"></script>\n</body>',
            )
        if "exercise-interactions.js" not in source:
            source = source.replace(
                '  <script src="./assets/validator-enhancements.js?v=semantic2"></script>',
                '  <script src="./assets/exercise-interactions.js?v=20"></script>\n'
                '  <script src="./assets/validator-enhancements.js?v=semantic2"></script>',
            )
        if "content/exercises.js" not in source:
            source = source.replace(
                '  <script src="./assets/exercise-interactions.js?v=2"></script>',
                '  <script src="./content/exercises.js?v=8"></script>\n'
                '  <script src="./assets/exercise-interactions.js?v=20"></script>',
            )
        source = source.replace("content/exercises.js?v=2", "content/exercises.js?v=3")
        source = source.replace("content/exercises.js?v=3", "content/exercises.js?v=4")
        source = source.replace("content/exercises.js?v=4", "content/exercises.js?v=5")
        source = source.replace("content/exercises.js?v=5", "content/exercises.js?v=6")
        source = source.replace("content/exercises.js?v=6", "content/exercises.js?v=7")
        source = source.replace("content/exercises.js?v=7", "content/exercises.js?v=8")
        source = source.replace("exercise-interactions.js?v=1", "exercise-interactions.js?v=2")
        source = source.replace("exercise-interactions.js?v=2", "exercise-interactions.js?v=3")
        source = source.replace("exercise-interactions.js?v=3", "exercise-interactions.js?v=4")
        source = source.replace("exercise-interactions.js?v=4", "exercise-interactions.js?v=5")
        source = source.replace("exercise-interactions.js?v=5", "exercise-interactions.js?v=6")
        source = source.replace("exercise-interactions.js?v=6", "exercise-interactions.js?v=7")
        source = source.replace("exercise-interactions.js?v=7", "exercise-interactions.js?v=8")
        source = source.replace("exercise-interactions.js?v=8", "exercise-interactions.js?v=9")
        source = source.replace("exercise-interactions.js?v=9", "exercise-interactions.js?v=10")
        source = source.replace("exercise-interactions.js?v=10", "exercise-interactions.js?v=11")
        source = source.replace("exercise-interactions.js?v=11", "exercise-interactions.js?v=12")
        source = source.replace("exercise-interactions.js?v=12", "exercise-interactions.js?v=13")
        source = source.replace("exercise-interactions.js?v=13", "exercise-interactions.js?v=14")
        source = source.replace("exercise-interactions.js?v=14", "exercise-interactions.js?v=15")
        source = source.replace("exercise-interactions.js?v=15", "exercise-interactions.js?v=16")
        source = source.replace("exercise-interactions.js?v=16", "exercise-interactions.js?v=17")
        source = source.replace("exercise-interactions.js?v=17", "exercise-interactions.js?v=18")
        source = source.replace("exercise-interactions.js?v=18", "exercise-interactions.js?v=19")
        source = source.replace("exercise-interactions.js?v=19", "exercise-interactions.js?v=20")
        target.write_text(source, encoding="utf-8")
        if border_cleanup_needed:
            art_file = ART_DIR / f"pg{page:03d}-art.png"
            art_image = Image.open(art_file).convert("RGB")
            remove_blue_border(art_image)
            art_image.save(art_file, compress_level=6)
    if border_cleanup_needed:
        border_marker.write_text(
            "Blue edge gradients removed from all generated artwork layers.\n",
            encoding="utf-8",
        )
    print(f"Built {len(report)} semantic pages and text-free art layers.")


if __name__ == "__main__":
    main()
