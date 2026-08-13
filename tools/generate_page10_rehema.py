import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
SEGMENTS = [
    ("Kutambua milio na sauti za vitu na wanyama mbalimbali.", None),
    ("Kazi ya kufanya.", None),
    ("Mwambie rafiki yako aigize au aoneshe ishara au alama za sauti na milio mbalimbali.", 0),
    ("Maswali.", None),
    ("Moja.", None),
    ("Je, rafiki yako ameigiza au ameonesha ishara au alama za mlio au sauti ya nini?", 1),
    ("Mbili.", None),
    ("Ulitumia kiungo gani kusikiliza au kuonesha ishara au alama za mlio au sauti hiyo?", 2),
    ("Vitu mbalimbali hutoa milio.", None),
    ("Mfano, kengele, ngoma, zeze, filimbi, debe na ubao.", None),
    ("Sauti zinatolewa na viumbe hai. Mfano, watu, wanyama, ndege na wadudu.", None),
    ("Tunasikiliza sauti na milio mbalimbali kwa kutumia masikio.", None),
    ("Wimbo wa sauti za wanyama mbalimbali.", None),
    ("Nyauu, nyauu. Hii sauti ya nini? Sauti ya paka. Paka, paka ni rafiki yetu anafukuza panya.", None),
    ("Wu, wu. Hii sauti ya nini? Sauti ya mbwa. Mbwa, mbwa ni rafiki yetu anatupa ulinzi.", None),
    ("Mee, mee. Hii sauti ya nini? Sauti ya mbuzi. Mbuzi, mbuzi ni rafiki yetu anatupa nyama na maziwa.", None),
    ("Moo, moo. Hii sauti ya nini? Sauti ya ng'ombe. Ng'ombe, ng'ombe ni rafiki yetu anatupa nyama na maziwa.", None),
    ("Zoezi la pili.", None),
    ("Moja. Je, ni vitu gani ukivitumia vinatoa sauti?", None),
    ("Mbili.", None),
    ("Chora au bainisha vitu vitatu vinavyotoa sauti.", 3),
    ("Tatu.", None),
    ("Taja majina ya wanyama unaoweza kubainisha au kuigiza sauti zao.", 4),
]
TEXT = " ".join(text for text, _ in SEGMENTS)


def normalize(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    return {"moja": "1", "kwanza": "1", "mbili": "2", "pili": "2", "tatu": "3"}.get(cleaned, cleaned)


def page_words():
    source = (ROOT / "pg010_sec001.html").read_text(encoding="utf-8")
    matches = re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', source, flags=re.S)
    return [(int(index), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for index, text in matches]


def map_source_indexes(cues):
    words = page_words()
    normalized = [normalize(text) for _, text in words]
    cursor = 0
    last_index = words[0][0] if words else 0
    for cue in cues:
        needle = normalize(cue["text"])
        found = next((p for p in range(cursor, len(words)) if normalized[p] == needle), -1)
        if found < 0:
            found = next((p for p in range(len(words)) if normalized[p] == needle), -1)
        if found >= 0:
            last_index = words[found][0]
            cursor = found + 1
        cue["sourceIndex"] = last_index


def add_patch_targets(cues):
    cursor = 0
    for text, target in SEGMENTS:
        count = len(re.findall(r"\S+", text))
        if isinstance(target, int):
            for word_index, cue in enumerate(cues[cursor:cursor + count]):
                cue["targetPatch"] = target
                cue["targetWord"] = word_index
        cursor += count


async def generate():
    output_dir = ROOT / "content" / "rehema"
    audio_name = "page-010-v9.mp3"
    cues = []
    with (output_dir / audio_name).open("wb") as audio:
        communicate = edge_tts.Communicate(TEXT, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in communicate.stream():
            if event["type"] == "audio":
                audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start = event["offset"] / 10_000_000
                duration = event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    map_source_indexes(cues)
    add_patch_targets(cues)
    entry = {"audio": audio_name, "voice": VOICE, "version": 9, "words": cues}
    (output_dir / "page-010.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    timecodes_path = output_dir / "timecodes.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    timecodes["10"] = entry
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"voice={VOICE} words={len(cues)} audio={(output_dir / audio_name).stat().st_size}")


if __name__ == "__main__":
    asyncio.run(generate())
