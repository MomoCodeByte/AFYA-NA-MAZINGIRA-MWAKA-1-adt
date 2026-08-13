import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
TEXT = " ".join([
    "Zoezi la nne.",
    "Jibu maswali haya.",
    "Oanisha sehemu ya mwili na kazi yake.",
    "Chora mistari kama ilivyooneshwa.",
    "Mfano, sikio, kusikia.",
    "Sehemu za mwili. Kazi zake.",
    "Kushika vitu. Kutembea. Kunusa. Kusikia. Kuongea na kula. Kuona.",
])


def normalize(value):
    cleaned = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"nne": "4"}.get(cleaned, cleaned)


def page_words():
    source = (ROOT / "pg013_sec001.html").read_text(encoding="utf-8")
    matches = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', source, flags=re.S)
    return [(int(i), html.unescape(re.sub(r"<[^>]+>", "", t)).strip()) for i, t in matches]


def map_indexes(cues):
    words = page_words()
    normalized = [normalize(t) for _, t in words]
    cursor, last = 0, 0
    for cue in cues:
        needle = normalize(cue["text"])
        found = next((p for p in range(cursor, len(words)) if normalized[p] == needle), -1)
        if found < 0:
            found = next((p for p in range(len(words)) if normalized[p] == needle), -1)
        if found >= 0:
            last, cursor = words[found][0], found + 1
        cue["sourceIndex"] = last


async def generate():
    out = ROOT / "content" / "rehema"
    audio_name = "page-013-v9.mp3"
    cues = []
    with (out / audio_name).open("wb") as audio:
        communicate = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in communicate.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    map_indexes(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 9, "words": cues}
    (out / "page-013.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    path = out / "timecodes.json"
    all_entries = json.loads(path.read_text(encoding="utf-8"))
    all_entries["13"] = entry
    path.write_text(json.dumps(all_entries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / audio_name).stat().st_size}")


if __name__ == "__main__": asyncio.run(generate())
