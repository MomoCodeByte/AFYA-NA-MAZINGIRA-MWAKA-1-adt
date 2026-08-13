import asyncio, json, re
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Kazi ya kufanya.", "source", [2, 3, 4]),
    ("Moja.", "source", [5]),
    ("Angalia na bainisha picha, kisha andika au taja jina la kila mmea.", "patch0", list(range(12))),
    ("Namba moja.", "number", [58]),
    ("Picha namba moja inaonesha mimea ya mahindi yenye mashina marefu, majani marefu na masuke.", "image", None),
    ("Namba mbili.", "number", [59]),
    ("Picha namba mbili inaonesha mmea wa nanasi wenye majani marefu yenye ncha kali na tunda la nanasi.", "image", None),
    ("Namba tatu.", "number", [56]),
    ("Picha namba tatu inaonesha mgomba wenye majani mapana na mkungu wa ndizi.", "image", None),
    ("Namba nne.", "number", [57]),
    ("Picha namba nne inaonesha mpapai wenye majani mapana na matunda ya papai.", "image", None),
    ("Mbili.", "source", [14]),
    ("Andika au taja majina ya mimea mingine mitano unayoifahamu.", "patch1", list(range(9))),
    ("Zoezi la pili.", "source", [22, 23, 24]),
    ("Jibu maswali haya.", "source", [25, 26, 27]),
    ("Moja. Viumbe hai wapo katika makundi mangapi? Yataje.", "source", list(range(28, 36))),
    ("Mbili. Mimea ina faida gani?", "source", list(range(36, 41))),
    ("Tatu. Taja mimea inayopatikana kwenye mazingira ya shule yako.", "source", list(range(41, 50))),
    ("Nne. Taja mimea minne inayotoa matunda.", "source", list(range(50, 56))),
]
TEXT = " ".join(text for text, _, _ in SEGMENTS)

def assign(cues):
    cursor = 0
    for text, kind, indexes in SEGMENTS:
        count = len(re.findall(r"\S+", text))
        part = cues[cursor:cursor + count]
        if kind.startswith("patch"):
            patch = int(kind[-1])
            for word, index in zip(part, indexes):
                word["targetPatch"] = patch
                word["targetWord"] = index
        elif kind == "source":
            for word, index in zip(part, indexes):
                word["sourceIndex"] = index
        elif kind == "number":
            for word in part[:-1]:
                word["targetImage"] = True
            if part:
                part[-1]["sourceIndex"] = indexes[0]
        else:
            for word in part:
                word["targetImage"] = True
        cursor += count

async def main():
    out = ROOT / "content" / "rehema"
    name = "page-065-v8.mp3"
    cues = []
    with (out / name).open("wb") as audio:
        stream = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio":
                audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start = event["offset"] / 10_000_000
                duration = event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    assign(cues)
    entry = {"audio": name, "voice": VOICE, "version": 8, "words": cues}
    (out / "page-065.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    timecodes = out / "timecodes.json"
    data = json.loads(timecodes.read_text(encoding="utf-8"))
    data["65"] = entry
    timecodes.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / name).stat().st_size}")

if __name__ == "__main__":
    asyncio.run(main())
