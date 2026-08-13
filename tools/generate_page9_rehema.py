import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Kazi za sehemu za nje za mwili wa binadamu.", None),
    ("Kiungo gani cha mwili kinatumika kuona vitu mbalimbali?", None),
    ("Zoezi la kwanza.", None),
    ("Taja rangi za maumbo uliyoyaona.", None),
    ("Umbo namba moja ni mraba wa rangi ya bluu. Umbo namba mbili ni pembetatu ya rangi nyekundu. Umbo namba tatu ni duara la rangi ya kijani. Umbo namba nne ni mstatili wa rangi ya waridi. Umbo namba tano ni mcheduara wa rangi ya njano.", "image"),
    ("a. Umbo namba moja lina rangi.", None),
    ("b. Umbo namba mbili lina rangi.", None),
    ("c. Umbo namba tatu lina rangi.", None),
    ("d. Umbo namba nne lina rangi.", None),
    ("e. Umbo namba tano lina rangi.", None),
    ("Macho humwezesha binadamu kuona.", None),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def normalize(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja": "1", "kwanza": "1", "mbili": "2", "pili": "2", "tatu": "3", "nne": "4", "tano": "5"}.get(cleaned, cleaned)


def page_words():
    source = (ROOT / "pg009_sec001.html").read_text(encoding="utf-8")
    matches = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', source, flags=re.S)
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
        if target == "image":
            for cue in cues[cursor:cursor + count]:
                cue["targetImage"] = True
        cursor += count


async def generate():
    output_dir = ROOT / "content" / "rehema"
    audio_name = "page-009-v10.mp3"
    cues = []
    with (output_dir / audio_name).open("wb") as audio:
        communicate = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in communicate.stream():
            if event["type"] == "audio":
                audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start = event["offset"] / 10_000_000
                duration = event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    map_source_indexes(cues)
    add_visual_targets(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 10, "words": cues}
    (output_dir / "page-009.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    timecodes_path = output_dir / "timecodes.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    timecodes["9"] = entry
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(output_dir / audio_name).stat().st_size}")


if __name__ == "__main__":
    asyncio.run(generate())
