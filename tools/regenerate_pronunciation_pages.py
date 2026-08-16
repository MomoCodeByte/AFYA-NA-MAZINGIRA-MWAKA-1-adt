import asyncio
import html
import json
import re
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
PAGES = [14, 19, 24, 31, 45, 47, 66]
NUMBER_WORDS = {"1": "Moja", "2": "Mbili", "3": "Tatu", "4": "Nne", "5": "Tano", "6": "Sita"}


def source_data(page):
    raw = (ROOT / f"pg{page:03d}_sec001.html").read_text(encoding="utf-8")
    transcript = re.search(r'<div class="accessible-transcript[^>]*>(.*?)</div>', raw, re.S).group(1)
    nodes = [(html.unescape(i), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in re.findall(r'data-id="([^"]+)"[^>]*>(.*?)</span>', transcript, re.S)]
    while nodes and ("AFYA NA MAZINGIRA" in nodes[-1][1] or re.fullmatch(r"\d+", nodes[-1][1])): nodes.pop()
    words = [(int(i), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', raw, re.S)]
    return nodes, words


def spoken(text):
    text = re.sub(r"\bGPE\b", "gipiee", text, flags=re.I)
    text = re.sub(r"\bKKKT\b", "kei kei kei ti", text, flags=re.I)
    text = re.sub(r"\bVVU\b", "Vivi yuu", text, flags=re.I)
    text = re.sub(r"(?:x|×|Ã—|\*)\s*2\b", "Rudia ubeti huu mara mbili", text, flags=re.I)
    match = re.fullmatch(r"([1-6])\.", text.strip())
    return NUMBER_WORDS[match.group(1)] + "." if match else text


def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    aliases = {"moja":"1", "mbili":"2", "tatu":"3", "nne":"4", "tano":"5", "sita":"6", "gipiee":"gpe", "kei":"kkkt", "ti":"kkkt", "vivi":"vvu", "yuu":"vvu", "rudia":"x", "ubeti":"x", "huu":"x", "mara":"x"}
    return aliases.get(value, value)


def map_cues(cues, words):
    normalized = [norm(text) for _, text in words]; cursor = last = 0
    for cue in cues:
        needle = norm(cue["text"])
        if needle in {"gpe", "kkkt"}:
            position = next((i for i in range(cursor, len(words)) if needle in normalized[i]), -1)
        else:
            position = next((i for i in range(cursor, len(words)) if normalized[i] == needle), -1)
        if position < 0: position = next((i for i in range(len(words)) if normalized[i] == needle), -1)
        if position >= 0: last, cursor = words[position][0], position + 1
        cue["sourceIndex"] = last


async def generate_page(page, all_entries):
    nodes, words = source_data(page); text = " ".join(spoken(value) for _, value in nodes); cues = []
    audio_name = f"page-{page:03d}-pronunciation-v11.mp3"; out = ROOT / "content" / "rehema"
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(text, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    map_cues(cues, words); entry = {"audio": audio_name, "voice": VOICE, "version": 11, "words": cues}
    (out / f"page-{page:03d}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    all_entries[str(page)] = entry
    print(f"page={page} words={len(cues)} audio={(out / audio_name).stat().st_size}")


async def main():
    path = ROOT / "content" / "rehema" / "timecodes.json"; entries = json.loads(path.read_text(encoding="utf-8"))
    pages = [int(value) for value in sys.argv[1:]] if len(sys.argv) > 1 else PAGES
    for page in pages: await generate_page(page, entries)
    path.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__": asyncio.run(main())
