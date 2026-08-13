import asyncio, json, re
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Zoezi la nne.", "source", [1, 2, 3]),
    ("Tazama na bainisha alama zifuatazo, kisha andika au eleza maana ya kila alama.", "patch", list(range(13))),
    ("Namba moja.", "number", [12]),
    ("Alama ya umeme mkubwa ni pembetatu ya njano yenye ukingo mweusi na mchoro wa radi. Inaonya kuhusu hatari ya umeme mkubwa.", "image", None),
    ("Namba mbili.", "number", [14]),
    ("Alama ya baiskeli ni pembetatu ya njano yenye ukingo mwekundu na mchoro wa baiskeli. Inaonya kuhusu sehemu ambayo waendesha baiskeli wanaweza kupita.", "image", None),
    ("Namba tatu.", "number", [13]),
    ("Alama ya watoto wanaovuka ni pembetatu yenye ukingo mwekundu na picha ya watoto wawili wakitembea. Inaonya kuhusu watoto wanaovuka barabara.", "image", None),
    ("Namba nne.", "number", [15]),
    ("Alama ya hatari ni pembetatu yenye ukingo mweusi na mchoro wa fuvu la kichwa pamoja na mifupa. Inaonya kuhusu kitu hatari au chenye sumu.", "image", None),
    ("Katika mazingira tunayoishi kuna viumbe hai mbalimbali.", "source", list(range(16, 23))),
    ("Viumbe hao ni kama vile paka, mbuzi, ng'ombe na miti.", "source", list(range(23, 33))),
    ("Katika sura ya tano utajifunza kuhusu viumbe hai wanaopatikana katika mazingira yetu.", "source", list(range(33, 45))),
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
    name = "page-060-v8.mp3"
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
    (out / "page-060.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    timecodes = out / "timecodes.json"
    data = json.loads(timecodes.read_text(encoding="utf-8"))
    data["60"] = entry
    timecodes.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / name).stat().st_size}")

if __name__ == "__main__":
    asyncio.run(main())
