import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Kisha mwalimu alitaja njia za kujikinga na maambukizi ya Vivi yuu.", None),
    ("Moja. Epuka kuchangia sindano unapopatiwa matibabu.", None),
    ("Mbili. Epuka kuchangia sindano unapotoga masikio.", None),
    ("Tatu. Funga vidonda wakati wote ili visitoe damu.", None),
    ("Nne. Epuka kugusa damu ya mtu mwingine.", None),
    ("Tano. Vaa glovu au mfuko wa plastiki unapomhudumia majeruhi.", None),
    ("Sita. Epuka kuchangia vifaa kama miswaki, dodoki na vitana.", None),
    ("Wimbo.", None),
    ("Vivi yuu ni Virusi vya Ukimwi. Rudia ubeti huu mara mbili. UKIMWI ni nini jamani? UKIMWI ni Upungufu wa Kinga Mwilini jamani. Rudia ubeti huu mara mbili.", None),
    ("Tusichangie wembe, sindano na mswaki. Rudia ubeti huu mara mbili. Tusichangie chanuo, kitana na pini. Rudia ubeti huu mara mbili. Tukichangia hivyo tutapata UKIMWI. Rudia ubeti huu mara mbili.", None),
    ("Maswali.", None),
    ("Moja. Ili kutambua kuwa umeambukizwa Vivi yuu unapaswa kufanya nini?", None),
    ("Mbili. Orodhesha vitu vitano ambavyo vikichangiwa husababisha maambukizi ya Vivi yuu.", None),
    ("Tatu.", None),
    ("Andika au bainisha njia tano za kujikinga na maambukizi ya Vivi yuu.", 0),
    ("Nne. Nini hatari ya kugusa damu ya mtu mwenye Vivi yuu?", None),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja":"1", "mbili":"2", "tatu":"3", "nne":"4", "tano":"5", "sita":"6", "mara":"x", "vivi":"vvu", "yuu":"vvu"}.get(value, value)


def words():
    source = (ROOT / "pg046_sec001.html").read_text(encoding="utf-8")
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
            for index, cue in enumerate(cues[cue_cursor:cue_cursor + count]): cue.update(targetPatch=target, targetWord=min(index, 10))
        cue_cursor += count


async def generate():
    out = ROOT / "content" / "rehema"; audio_name = "page-046-v10.mp3"; cues = []
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    prepare(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 10, "words": cues}
    (out / "page-046.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    path = out / "timecodes.json"; data = json.loads(path.read_text(encoding="utf-8")); data["46"] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / audio_name).stat().st_size}")


if __name__ == "__main__": asyncio.run(generate())
