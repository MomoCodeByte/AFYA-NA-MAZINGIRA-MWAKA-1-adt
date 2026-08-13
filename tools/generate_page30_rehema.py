import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Kazi ya kufanya.", None),
    ("Fuata hatua za kukata kucha.", None),
    ("Kata kucha kwa kutumia mojawapo ya vifaa hivi.", None),
    ("Moja. Wembe. Mbili. Mkasi. Tatu. Kikata kucha.", None),
    ("Zoezi la tatu.", None),
    ("Moja. Taja vifaa vinavyotumika kukatia kucha.", None),
    ("Mbili. Kucha ndefu zinahifadhi nini?", None),
    ("Tatu. Ukichangia vifaa vya kukatia kucha utapata madhara gani?", None),
    ("Nne. Kwa nini tunakata kucha?", None),
    ("Kutunza nywele.", None),
    ("Angalia na bainisha picha zifuatazo, kisha jibu maswali.", 0),
    ("Picha namba moja inaonesha mtoto mwenye nywele safi, fupi na zilizopangwa vizuri. Picha namba mbili inaonesha mtoto mwenye nywele chafu, ndefu na zisizopangwa vizuri.", "image"),
    ("Moja. Taja tofauti ya picha namba moja na mbili.", None),
    ("Mbili. Picha gani inakuvutia? Kwa nini?", None),
    ("Tatu. Picha ya mtoto yupi inayofaa kuigwa?", None),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja":"1", "mbili":"2", "tatu":"3", "nne":"4"}.get(value, value)


def words():
    source = (ROOT / "pg030_sec001.html").read_text(encoding="utf-8")
    found = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', source, re.S)
    return [(int(i), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in found]


def map_cues(cues):
    source = words(); normalized = [norm(text) for _, text in source]; cursor = last = 0
    for cue in cues:
        needle = norm(cue["text"])
        position = next((i for i in range(cursor, len(source)) if normalized[i] == needle), -1)
        if position < 0: position = next((i for i in range(len(source)) if normalized[i] == needle), -1)
        if position >= 0: last, cursor = source[position][0], position + 1
        cue["sourceIndex"] = last


def visual_targets(cues):
    cursor = 0
    for text, target in SEGMENTS:
        count = len(re.findall(r"\S+", text))
        if isinstance(target, int):
            for index, cue in enumerate(cues[cursor:cursor + count]): cue.update(targetPatch=target, targetWord=index)
        elif target == "image":
            for cue in cues[cursor:cursor + count]: cue["targetImage"] = True
        cursor += count


async def generate():
    out = ROOT / "content" / "rehema"; audio_name = "page-030-v9.mp3"; cues = []
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    map_cues(cues); visual_targets(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 9, "words": cues}
    (out / "page-030.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    path = out / "timecodes.json"; data = json.loads(path.read_text(encoding="utf-8")); data["30"] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / audio_name).stat().st_size}")


if __name__ == "__main__": asyncio.run(generate())
