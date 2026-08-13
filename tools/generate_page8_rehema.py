import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Sehemu za nje za mwili wa binadamu.", None),
    ("Angalia na bainisha picha hii, kisha jibu swali.", 0),
    ("Picha inaonesha mtoto wa kiume akiwa amesimama na kunyoosha mikono. Mistari inaelekeza sehemu za nje za mwili kama kichwa, macho, masikio, pua, mdomo, mikono, vidole, tumbo, miguu na nyayo.", "image"),
    ("Taja sehemu za nje za mwili wa binadamu.", None),
    ("Kazi ya kufanya.", None),
    ("Chora au taja mwili wa binadamu na uoneshe sehemu za nje za mwili.", 1),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9à-ɏ]+", "", value.lower())


def page_words():
    source = (ROOT / "pg008_sec001.html").read_text(encoding="utf-8")
    matches = re.findall(
        r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>',
        source,
        flags=re.S,
    )
    return [(int(index), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for index, text in matches]


def map_source_indexes(cues):
    words = page_words()
    normalized = [normalize(text) for _, text in words]
    cursor = 0
    last_index = words[0][0] if words else 0
    for cue in cues:
        needle = normalize(cue["text"])
        found = -1
        for position in range(cursor, len(words)):
            if normalized[position] == needle:
                found = position
                break
        if found < 0:
            for position in range(len(words)):
                if normalized[position] == needle:
                    found = position
                    break
        if found >= 0:
            last_index = words[found][0]
            cursor = found + 1
        cue["sourceIndex"] = last_index


def add_visual_targets(cues):
    cursor = 0
    for text, target in SEGMENTS:
        count = len(re.findall(r"\S+", text))
        for word_index, cue in enumerate(cues[cursor:cursor + count]):
            if isinstance(target, int):
                cue["targetPatch"] = target
                cue["targetWord"] = word_index
            elif target == "image":
                cue["targetImage"] = True
        cursor += count


async def generate():
    output_dir = ROOT / "content" / "rehema"
    audio_path = output_dir / "page-008-v9.mp3"
    cues_path = output_dir / "page-008.json"
    cues = []
    with audio_path.open("wb") as audio:
        communicate = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in communicate.stream():
            if event["type"] == "audio":
                audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start = event["offset"] / 10_000_000
                duration = event["duration"] / 10_000_000
                cues.append({
                    "text": event["text"],
                    "start": round(start, 6),
                    "end": round(start + duration, 6),
                })
    map_source_indexes(cues)
    add_visual_targets(cues)
    entry = {"audio": "page-008-v9.mp3", "voice": VOICE, "version": 9, "words": cues}
    cues_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    timecodes_path = output_dir / "timecodes.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    timecodes["8"] = entry
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={audio_path.stat().st_size}")


if __name__ == "__main__":
    asyncio.run(generate())
