import asyncio, json, re
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Sura ya tano.", "source", [2, 3, 4]),
    ("Viumbe hai katika mazingira.", "source", list(range(5, 9))),
    ("Utangulizi.", "source", [9]),
    ("Katika sura hii utajifunza kuhusu viumbe hai. Utaweza kubaini aina mbalimbali ya wanyama na mimea. Vilevile utaelezea faida za wanyama na mimea katika maisha yako ya kila siku.", "source", list(range(10, 38))),
    ("Picha za utangulizi zinaonesha mimea mitatu. Mmea wa kwanza ni alizeti yenye ua kubwa la njano. Mmea wa pili ni mpapai wenye matunda ya papai. Mmea wa tatu ni mgomba wenye mkungu wa ndizi. Chini yake kuna farasi wa rangi ya kahawia na mbuzi mwenye rangi ya kahawia na nyeupe.", "image", None),
    ("Kazi ya kufanya.", "source", list(range(38, 41))),
    ("Elezea kwa kifupi vitu ulivyobainisha na unavyoviona katika picha.", "patch", list(range(9))),
    ("Kutambua wanyama mbalimbali.", "source", list(range(48, 51))),
    ("Paka.", "source", [51]),
    ("Picha ya paka inaonesha paka mwenye mistari myeusi na kijivu, masikio mawili, miguu minne na mkia mrefu.", "image", None),
    ("Mjusi.", "source", [52]),
    ("Picha ya mjusi inaonesha mjusi mwenye miguu minne na mkia mrefu uliopinda.", "image", None),
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
        else:
            for word in part:
                word["targetImage"] = True
        cursor += count

async def main():
    out = ROOT / "content" / "rehema"
    name = "page-061-v8.mp3"
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
    (out / "page-061.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    timecodes = out / "timecodes.json"
    data = json.loads(timecodes.read_text(encoding="utf-8"))
    data["61"] = entry
    timecodes.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / name).stat().st_size}")

if __name__ == "__main__":
    asyncio.run(main())
