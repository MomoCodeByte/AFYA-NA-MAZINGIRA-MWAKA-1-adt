import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Kusafisha choo.", None),
    ("Kwa nini tusafishe choo?", None),
    ("Tunasafisha choo kuepuka magonjwa kama kuharisha na kipindupindu. Pia kuondoa harufu mbaya.", None),
    ("Choo kisafishwe kwa maji, sabuni na dawa. Baada ya kusafisha choo tunawe mikono. Tutumie maji safi na sabuni.", None),
    ("Zoezi la kumi na moja.", None),
    ("Moja.", None),
    ("Andika au bainisha vifaa vitatu vinavyotumika kusafisha choo.", 0),
    ("Mbili. Taja wadudu wanaopenda kuishi chooni.", None),
    ("Tatu. Taja aina za vyoo unavyovifahamu.", None),
    ("Nne.", None),
    ("Andika au bainisha magonjwa mawili utakayopata ukitumia choo.", 1),
    ("Kichafu.", None),
    ("Tano. Choo kinachotumika shuleni kwenu ni cha aina gani?", None),
    ("Sita. Eleza umuhimu wa kujisafisha baada ya kujisaidia.", None),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja":"1", "mbili":"2", "tatu":"3", "nne":"4", "tano":"5", "sita":"6"}.get(value, value)


def words():
    source = (ROOT / "pg044_sec001.html").read_text(encoding="utf-8")
    found = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', source, re.S)
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
    out = ROOT / "content" / "rehema"; audio_name = "page-044-v9.mp3"; cues = []
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    prepare(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 9, "words": cues}
    (out / "page-044.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    path = out / "timecodes.json"; data = json.loads(path.read_text(encoding="utf-8")); data["44"] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / audio_name).stat().st_size}")


if __name__ == "__main__": asyncio.run(generate())
