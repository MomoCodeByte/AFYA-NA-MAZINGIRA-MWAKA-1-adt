import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Hatua za kupiga nguo pasi.", None),
    ("Moja. Kijana wa kiume anatandika na kunyoosha nguo juu ya meza ili kuiandaa kwa kupigwa pasi.", "image"),
    ("Mbili. Kijana wa kiume anachomeka pasi ya umeme kwenye soketi, huku kijana wa kike akiweka makaa ya moto ndani ya pasi ya mkaa.", "image"),
    ("Tatu. Kijana wa kiume anapiga nguo pasi kwa kutumia pasi ya umeme, huku kijana wa kike akipiga nguo nyingine kwa kutumia pasi ya mkaa. Wote wameweka nguo kwenye sehemu tambarare.", "image"),
    ("Nne. Kijana wa kike anatundika nguo zilizopigwa pasi kwenye vibanio vya nguo ili zihifadhiwe vizuri na zisikunje.", "image"),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja":"1", "mbili":"2", "tatu":"3", "nne":"4"}.get(value, value)


def words():
    source = (ROOT / "pg038_sec001.html").read_text(encoding="utf-8")
    found = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', source, re.S)
    return [(int(i), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in found]


def prepare(cues):
    source = words(); normalized = [norm(text) for _, text in source]; cursor = last = 0
    for cue in cues:
        needle = norm(cue["text"]); position = next((i for i in range(cursor, len(source)) if normalized[i] == needle), -1)
        if position < 0: position = next((i for i in range(len(source)) if normalized[i] == needle), -1)
        if position >= 0: last, cursor = source[position][0], position + 1
        cue["sourceIndex"] = last
    offset = len(re.findall(r"\S+", SEGMENTS[0][0]))
    for cue in cues[offset:]: cue["targetImage"] = True


async def generate():
    out = ROOT / "content" / "rehema"; audio_name = "page-038-v11.mp3"; cues = []
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    prepare(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 11, "words": cues}
    (out / "page-038.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    path = out / "timecodes.json"; data = json.loads(path.read_text(encoding="utf-8")); data["38"] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / audio_name).stat().st_size}")


if __name__ == "__main__": asyncio.run(generate())
