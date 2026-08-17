import asyncio, json, re
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "content" / "rehema"
VOICE = "sw-TZ-RehemaNeural"
AUDIO = "page-013-matching-v15.mp3"
VERSION = 15

segments = [
    ("Zoezi la nne.", 1),
    ("Jibu maswali haya.", 4),
    ("Oanisha sehemu ya mwili na kazi yake. Mfano, sikio linaoanishwa na kusikia.", 7),
    ("Zoezi lina sehemu sita za mwili na kazi sita. Chagua sehemu ya mwili, kisha chagua kazi inayolingana nayo.", "image"),
    ("Picha ya kwanza inaonesha macho.", "image"),
    ("Picha ya pili inaonesha mdomo.", "image"),
    ("Picha ya tatu inaonesha sikio.", "image"),
    ("Picha ya nne inaonesha miguu.", "image"),
    ("Picha ya tano inaonesha mikono.", "image"),
    ("Picha ya sita inaonesha pua.", "image"),
    ("Kazi zinazopatikana ni hizi.", "image"),
    ("Moja. Kushika vitu.", 27),
    ("Mbili. Kutembea.", 29),
    ("Tatu. Kunusa.", 30),
    ("Nne. Kusikia.", 31),
    ("Tano. Kuongea na kula.", 32),
    ("Sita. Kuona.", 35),
    ("Chagua sehemu ya mwili, kisha chagua kazi yake.", "image"),
    ("Mwili uweze kukua vizuri unahitaji afya bora. Katika sura ya pili tutajifunza kuhusu afya bora katika mwili wa binadamu.", 37),
]

async def main():
    text = " ".join(s[0] for s in segments)
    cues = []
    with (OUT / AUDIO).open("wb") as audio:
        stream = edge_tts.Communicate(text, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio":
                audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start = event["offset"] / 10_000_000
                duration = event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    cursor = 0
    for sentence, target in segments:
        count = len(re.findall(r"\S+", sentence))
        for cue in cues[cursor:cursor + count]:
            if target == "image":
                cue["targetImage"] = True
            else:
                cue["sourceIndex"] = target
        cursor += count
    entry = {"audio": AUDIO, "voice": VOICE, "version": VERSION, "words": cues}
    (OUT / "page-013.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    timecodes = OUT / "timecodes.json"
    data = json.loads(timecodes.read_text(encoding="utf-8"))
    data["13"] = entry
    timecodes.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"audio={AUDIO} words={len(cues)} bytes={(OUT / AUDIO).stat().st_size}")

asyncio.run(main())
