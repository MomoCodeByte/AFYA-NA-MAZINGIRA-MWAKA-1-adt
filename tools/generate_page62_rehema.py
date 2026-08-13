import asyncio, json, re
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Chui.", "source", [12]),
    ("Picha inaonesha chui wa rangi ya manjano mwenye madoa meusi, miguu minne na mkia mrefu.", "image", None),
    ("Chura.", "source", [13]),
    ("Picha inaonesha chura wa rangi ya kahawia akiwa amekaa.", "image", None),
    ("Mamba.", "source", [14]),
    ("Picha inaonesha mamba mwenye mdomo mrefu, meno makali, miguu minne na mkia mrefu.", "image", None),
    ("Ng'ombe.", "source", [15]),
    ("Picha inaonesha ng'ombe wa rangi ya kahawia mwenye pembe mbili, miguu minne na mkia.", "image", None),
    ("Tembo.", "source", [16]),
    ("Picha inaonesha tembo mkubwa mwenye masikio mapana, meno mawili marefu, miguu minne na mkonga mrefu.", "image", None),
    ("Kazi ya kufanya.", "source", [1, 2, 3]),
    ("Andika au bainisha majina ya wanyama waliopo katika picha hizi.", "patch", list(range(10))),
    ("Namba moja.", "number", [17]),
    ("Picha namba moja inaonesha panya mwenye masikio mawili, miguu minne na mkia mrefu.", "image", None),
    ("Namba mbili.", "number", [18]),
    ("Picha namba mbili inaonesha simba dume mwenye manyoya mengi shingoni, miguu minne na mkia mrefu.", "image", None),
]
TEXT = " ".join(text for text, _, _ in SEGMENTS)

def assign(cues):
    cursor = 0
    for text, kind, indexes in SEGMENTS:
        count = len(re.findall(r"\S+", text))
        part = cues[cursor:cursor + count]
        if kind == "patch":
            for word, index in zip(part, indexes):
                word["targetPatch"] = 0
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
    name = "page-062-v8.mp3"
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
    (out / "page-062.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    timecodes = out / "timecodes.json"
    data = json.loads(timecodes.read_text(encoding="utf-8"))
    data["62"] = entry
    timecodes.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / name).stat().st_size}")

if __name__ == "__main__":
    asyncio.run(main())
