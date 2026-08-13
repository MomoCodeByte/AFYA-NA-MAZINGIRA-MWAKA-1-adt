import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Vyakula vinavyoliwa mchana.", None),
    ("Vyakula vinavyoliwa jioni.", None),
    ("Zoezi la kwanza.", None),
    ("Moja. Taja vyakula unavyokula asubuhi, mchana na jioni.", None),
    ("Mbili. Eleza ni kwa nini tunakula chakula.", None),
    ("Tatu.", None),
    ("Chora au bainisha vyakula unavyopenda kula.", 0),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja": "1", "kwanza": "1", "mbili": "2", "tatu": "3"}.get(value, value)


def source_words():
    source = (ROOT / "pg015_sec001.html").read_text(encoding="utf-8")
    found = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', source, re.S)
    return [(int(i), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in found]


def map_cues(cues):
    words = source_words()
    normalized = [norm(text) for _, text in words]
    cursor = last = 0
    for cue in cues:
        needle = norm(cue["text"])
        position = next((i for i in range(cursor, len(words)) if normalized[i] == needle), -1)
        if position < 0: position = next((i for i in range(len(words)) if normalized[i] == needle), -1)
        if position >= 0: last, cursor = words[position][0], position + 1
        cue["sourceIndex"] = last


def patch_targets(cues):
    cursor = 0
    for text, target in SEGMENTS:
        count = len(re.findall(r"\S+", text))
        if isinstance(target, int):
            for word_index, cue in enumerate(cues[cursor:cursor + count]):
                cue["targetPatch"], cue["targetWord"] = target, word_index
        cursor += count


async def generate():
    out = ROOT / "content" / "rehema"
    audio_name = "page-015-v9.mp3"
    cues = []
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    map_cues(cues)
    patch_targets(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 9, "words": cues}
    (out / "page-015.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    path = out / "timecodes.json"
    data = json.loads(path.read_text(encoding="utf-8")); data["15"] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / audio_name).stat().st_size}")


if __name__ == "__main__": asyncio.run(generate())
