import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Kumi na moja. Endelea kumwagilia mpaka miche ikue.", None),
    ("Maswali.", None),
    ("Moja. Kwa nini tunafunika kitalu baada ya kusia mbegu?", None),
    ("Mbili. Zipo mbegu zinazopandwa moja kwa moja kwenye mashimo. Taja majina matano ya mbegu hizo.", None),
    ("Tatu. Kwa nini tunamwagilia miche baada ya kupanda kwenye shimo?", None),
    ("Kazi ya kufanya.", None),
    ("Moja. Sia mbegu kwenye kitalu kilichoandaliwa.", None),
    ("Mbili. Otesha mche mmoja shuleni kwa kufuata hatua. Vilevile, otesha mche mwingine nyumbani kwa kufuata hatua.", None),
    ("Tatu. Mwagilia miche kila siku hadi ikue.", None),
    ("Nne.", None),
    ("Andika au eleza kwa ufupi ulichojifunza tangu umeotesha mti hadi umekua kwa kuonesha changamoto na mafanikio.", 0),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja":"1", "mbili":"2", "tatu":"3", "nne":"4"}.get(value, value)


def words():
    raw = (ROOT / "pg053_sec001.html").read_text(encoding="utf-8")
    found = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', raw, re.S)
    return [(int(i), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in found]


def prepare(cues):
    source = words(); normalized = [norm(text) for _, text in source]; cursor = last = cue_cursor = 0
    for cue in cues:
        needle = norm(cue["text"]); position = next((i for i in range(cursor, len(source)) if normalized[i] == needle), -1)
        if position < 0: position = next((i for i in range(len(source)) if normalized[i] == needle), -1)
        if position >= 0: last, cursor = source[position][0], position + 1
        cue["sourceIndex"] = last
    for text, target in SEGMENTS:
        count = len(re.findall(r"\S+", text))
        if isinstance(target, int):
            for index, cue in enumerate(cues[cue_cursor:cue_cursor + count]): cue.update(targetPatch=target, targetWord=index)
        cue_cursor += count


async def generate():
    out = ROOT / "content" / "rehema"; audio_name = "page-053-v10.mp3"; cues = []
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    prepare(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 10, "words": cues}
    (out / "page-053.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    path = out / "timecodes.json"; data = json.loads(path.read_text(encoding="utf-8")); data["53"] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / audio_name).stat().st_size}")


if __name__ == "__main__": asyncio.run(generate())
