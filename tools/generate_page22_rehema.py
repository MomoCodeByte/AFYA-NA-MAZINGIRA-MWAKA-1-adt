import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
TEXT = " ".join([
    "Wimbo.",
    "Moja. Usile tunda bila kuosha, utaumwa tumbo. Rudia ubeti huu mara mbili.",
    "Mbili. Usile tunda bila kuosha, utatapika. Rudia ubeti huu mara mbili.",
    "Tatu. Usile tunda bila kuosha, utaharisha. Rudia ubeti huu mara mbili.",
    "Zoezi la nne.",
    "Moja. Unatumia vifaa gani katika kuosha matunda?",
    "Mbili. Taja madhara matatu utakayopata ukila tunda bila kuliosha.",
    "Mazoezi ya viungo.",
    "Tunashauriwa kufanya mazoezi ya viungo kila siku.",
    "Mazoezi husaidia kujenga na kuimarisha misuli. Hivyo, hufanya mwili kuwa mkakamavu na wenye afya bora.",
    "Mchezo wa mpira wa mguu. Mchezo wa mdako. Mchezo wa mpira wa pete. Mchezo wa dama.",
])


def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja": "1", "mbili": "2", "tatu": "3", "nne": "4", "mara": "x"}.get(value, value)


def words():
    source = (ROOT / "pg022_sec001.html").read_text(encoding="utf-8")
    found = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', source, re.S)
    return [(int(i), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in found]


def map_cues(cues):
    source = words(); normalized = [norm(text) for _, text in source]
    cursor = last = 0
    for cue in cues:
        needle = norm(cue["text"])
        position = next((i for i in range(cursor, len(source)) if normalized[i] == needle), -1)
        if position < 0: position = next((i for i in range(len(source)) if normalized[i] == needle), -1)
        if position >= 0: last, cursor = source[position][0], position + 1
        cue["sourceIndex"] = last
    # The PDF stores the first row right-to-left in source order. Bind the
    # four game captions explicitly so highlighting follows the visual order.
    game_indexes = [74, 75, 76, 77, 78, 71, 72, 73, 79, 80, 81, 82, 83, 84, 85, 86]
    for cue, source_index in zip(cues[-len(game_indexes):], game_indexes):
        cue["sourceIndex"] = source_index


async def generate():
    out = ROOT / "content" / "rehema"; audio_name = "page-022-v11.mp3"; cues = []
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    map_cues(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 11, "words": cues}
    (out / "page-022.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    path = out / "timecodes.json"; data = json.loads(path.read_text(encoding="utf-8")); data["22"] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(out / audio_name).stat().st_size}")


if __name__ == "__main__": asyncio.run(generate())
