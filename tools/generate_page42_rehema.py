import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Matumizi sahihi ya choo.", None),
    ("Picha ya mtoto yupi anatumia choo kwa usahihi?", None),
    ("Picha namba moja inaonesha kijana wa kiume akikojoa sakafuni karibu na choo. Pembeni kuna ndoo ya kuhifadhia maji ya chooni ambayo haijafunikwa. Matumizi hayo si sahihi. Picha namba mbili inaonesha kijana wa kiume akikojoa ndani ya tundu la choo cha shimo kwa usahihi. Pembeni kuna ndoo ya kuhifadhia maji ya chooni iliyofunikwa vizuri.", "image"),
    ("Choo ni muhimu kwa matumizi ya binadamu. Choo kitumike kwa usahihi ili kuepuka magonjwa. Magonjwa hayo ni kama vile kipindupindu, kuhara na minyoo.", None),
    ("Pia choo bora husaidia kuhifadhi mazingira na vyanzo vya maji. Kuna aina mbalimbali za vyoo. Mfano, kuna vyoo vya shimo na vya kuvuta. Vyoo vya kuvuta hutiririsha maji yanayoondosha kinyesi.", None),
    ("Hatua sahihi za matumizi ya choo.", None),
    ("Picha ya chini inaonesha kijana wa kiume akifunika tundu la choo cha shimo baada ya kutumia choo. Haya ni matumizi sahihi ya choo.", "image"),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja":"1", "mbili":"2"}.get(value, value)


def words():
    source = (ROOT / "pg042_sec001.html").read_text(encoding="utf-8")
    found = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', source, re.S)
    return [(int(i), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in found]


def prepare(cues):
    source = words(); normalized = [norm(text) for _, text in source]; cursor = last = 0; cue_cursor = 0
    for cue in cues:
        needle = norm(cue["text"]); position = next((i for i in range(cursor, len(source)) if normalized[i] == needle), -1)
        if position < 0: position = next((i for i in range(len(source)) if normalized[i] == needle), -1)
        if position >= 0: last, cursor = source[position][0], position + 1
        cue["sourceIndex"] = last
    for text, target in SEGMENTS:
        count = len(re.findall(r"\S+", text))
        if target == "image":
            for cue in cues[cue_cursor:cue_cursor + count]: cue["targetImage"] = True
        cue_cursor += count


async def generate():
    out = ROOT / "content" / "rehema"; audio_name = "page-042-v11.mp3"; cues = []
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    prepare(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 11, "words": cues}
    (out / "page-042.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    path = out / "timecodes.json"; data = json.loads(path.read_text(encoding="utf-8")); data["42"] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / audio_name).stat().st_size}")


if __name__ == "__main__": asyncio.run(generate())
