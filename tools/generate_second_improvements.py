import asyncio, html, json, re
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
PAGES = [8, 9, 12, 17, 31, 35, 36, 37, 41, 49, 50, 71]
NUMBER_WORDS = {str(i): word for i, word in enumerate(["Sifuri", "Moja", "Mbili", "Tatu", "Nne", "Tano", "Sita", "Saba", "Nane", "Tisa", "Kumi"], 0)}

CONFIG = {
    8: {"replace": {"pg008_n0002": "Angalia na bainisha picha hii, kisha jibu swali.", "pg008_n0005": "Chora au chunguza mwili wa binadamu na uoneshe sehemu za nje za mwili"}, "remove": {"pg008_n0006"}, "patch": {"pg008_n0002": 0, "pg008_n0005": 1}, "after": {"pg008_n0002": ["Picha inaonesha mtoto wa kiume akiwa amesimama na kunyoosha mikono. Mistari inaelekeza kichwa, macho, masikio, pua, mdomo, mikono, vidole, tumbo, miguu na nyayo."]}},
    9: {"after": {"pg009_n0009": ["Katika swali la kwanza, umbo namba 1 ni mraba wa rangi ya bluu. Umbo namba 2 ni pembetatu ya rangi nyekundu. Umbo namba 3 ni duara la rangi ya kijani. Umbo namba 4 ni mstatili wa rangi ya waridi. Umbo namba 5 ni mcheduara wa rangi ya njano."]}},
    12: {"replace": {"pg012_n0012": "Andika au bainisha vitu vitatu vinavyotoa harufu mbaya.", "pg012_n0014": "Andika au bainisha vitu vinne vinavyotoa harufu nzuri."}, "patch": {"pg012_n0012": 0, "pg012_n0014": 1}},
    17: {"replace": {"pg017_n0005": "Andika au bainisha vifaa mnavyotumia nyumbani kwenu kutunzia chakula.", "pg017_n0011": "Orodhesha au bainisha mifano miwili ya magonjwa yanayotokana na kula chakula kisichotunzwa vizuri."}, "remove": {"pg017_n0006", "pg017_n0012"}, "patch": {"pg017_n0005": 0, "pg017_n0011": 1}},
    31: {"replace": {"pg031_n0025": "Andika au bainisha faida nne za kunyoa nywele."}, "patch": {"pg031_n0025": 0}},
    35: {"replace": {"pg035_n0002": "Angalia na bainisha picha namba 1 hadi 5, kisha fanya zoezi la 6."}, "patch": {"pg035_n0002": 0}, "after": {"pg035_n0005": ["Picha namba 1 inaonesha mtoto akitenganisha nguo nyeupe na nguo za rangi. Picha namba 2 inaonesha mtoto akifikicha nguo kwa sabuni ndani ya beseni. Picha namba 3 inaonesha mtoto akisuuza nguo kwa maji safi. Picha namba 4 inaonesha mtoto akikamua nguo ili kuondoa maji."]}},
    36: {"replace": {"pg036_n0003": "Panga na bainisha sentensi kwa mtiririko wa matukio katika picha."}, "patch": {"pg036_n0003": 0}, "after": {"pg036_n0001": ["Picha namba 5 inaonesha mtoto akianika nguo kwenye kamba na kuzibana kwa vibanio ili zikauke."]}},
    37: {"replace": {"pg037_n0003": "Andika au bainisha sababu tatu za kufua nguo."}, "patch": {"pg037_n0003": 0}},
    41: {"replace": {"pg041_n0010": "Andika au bainisha majina ya vyombo ulivyowahi kuviosha."}, "patch": {"pg041_n0010": 0}},
    49: {"replace": {"pg049_n0011": "Tazama na bainisha picha hii kisha jibu maswali."}, "patch": {"pg049_n0011": 0}, "after": {"pg049_n0011": ["Picha inaonesha wanafunzi wakisafisha mazingira ya shule. Kijana wa kiume anafagia njia kwa ufagio. Kijana wa kike anakusanya majani kwa reki. Kijana mwingine wa kike anatunza kichaka, na kijana wa kiume anabeba matawi yaliyokusanywa."]}},
    50: {"after": {"pg050_n0004": ["Vifaa vilivyo kwenye safu ya kulia kuanzia juu ni jembe, reki, mkasi wa kukatia maua, ufagio, koleo la takataka na pipa la takataka."]}},
    71: {"replace": {"pg071_n0002": "Andika au tunga sentensi nne kwa kufuata mtiririko wa picha."}, "patch": {"pg071_n0002": 0}},
}

def source_data(page):
    raw = (ROOT / f"pg{page:03d}_sec001.html").read_text(encoding="utf-8")
    transcript = re.search(r'<div class="accessible-transcript[^>]*>(.*?)</div>', raw, re.S).group(1)
    nodes = [(i, html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in re.findall(r'data-id="([^"]+)"[^>]*>(.*?)</span>', transcript, re.S)]
    while nodes and ("AFYA NA MAZINGIRA" in nodes[-1][1] or re.fullmatch(r"\d+", nodes[-1][1])):
        nodes.pop()
    words = [(int(i), html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>', raw, re.S)]
    return nodes, words

def spoken(text):
    text = re.sub(r"\bGPE\b", "gipiee", text, flags=re.I)
    text = re.sub(r"\bKKKT\b", "kei kei kei ti", text, flags=re.I)
    text = re.sub(r"\bVVU\b", "Vivi yuu", text, flags=re.I)
    text = re.sub(r"(?:x|Ã—|Ãƒâ€”|\*)\s*2\b", "Rudia ubeti huu mara mbili", text, flags=re.I)
    match = re.fullmatch(r"(\d+)\.", text.strip())
    return NUMBER_WORDS.get(match.group(1), match.group(1)) + "." if match else text

def norm(value):
    value = re.sub(r"[^a-z0-9\u00c0-\u024f]+", "", value.lower())
    aliases = {"moja":"1", "mbili":"2", "tatu":"3", "nne":"4", "tano":"5", "sita":"6", "saba":"7", "nane":"8", "tisa":"9", "kumi":"10", "gipiee":"gpe", "kei":"kkkt", "ti":"kkkt", "vivi":"vvu", "yuu":"vvu"}
    return aliases.get(value, value)

def map_source(cues, words, state):
    normalized = [norm(text) for _, text in words]
    for cue in cues:
        needle = norm(cue["text"])
        position = next((i for i in range(state["cursor"], len(words)) if normalized[i] == needle), -1)
        if position < 0:
            position = next((i for i in range(len(words)) if normalized[i] == needle), -1)
        if position >= 0:
            state["last"], state["cursor"] = words[position][0], position + 1
        cue["sourceIndex"] = state["last"]

async def generate_page(page, entries):
    config = CONFIG[page]; nodes, words = source_data(page); segments = []
    for node_id, original in nodes:
        if node_id in config.get("remove", set()):
            continue
        text = config.get("replace", {}).get(node_id, original)
        segments.append((spoken(text), "patch" if node_id in config.get("patch", {}) else "source", config.get("patch", {}).get(node_id)))
        for description in config.get("after", {}).get(node_id, []):
            segments.append((spoken(description), "image", None))
    full_text = " ".join(text for text, _, _ in segments); cues = []; out = ROOT / "content" / "rehema"; audio_name = f"page-{page:03d}-second-v12.mp3"
    with (out / audio_name).open("wb") as audio:
        stream = edge_tts.Communicate(full_text, VOICE, rate="-8%", boundary="WordBoundary")
        async for event in stream.stream():
            if event["type"] == "audio": audio.write(event["data"])
            elif event["type"] == "WordBoundary":
                start, duration = event["offset"] / 10_000_000, event["duration"] / 10_000_000
                cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    offset = 0; state = {"cursor": 0, "last": 0}
    for text, kind, patch in segments:
        count = len(re.findall(r"\S+", text)); part = cues[offset:offset + count]
        if kind == "patch":
            for index, cue in enumerate(part): cue.update({"targetPatch": patch, "targetWord": index})
        elif kind == "image":
            for cue in part: cue["targetImage"] = True
        else:
            map_source(part, words, state)
        offset += count
    entry = {"audio": audio_name, "voice": VOICE, "version": 12, "words": cues}
    (out / f"page-{page:03d}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8"); entries[str(page)] = entry
    print(f"page={page} words={len(cues)} audio={(out / audio_name).stat().st_size}")

async def main():
    path = ROOT / "content" / "rehema" / "timecodes.json"; entries = json.loads(path.read_text(encoding="utf-8"))
    for page in PAGES: await generate_page(page, entries)
    path.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

if __name__ == "__main__": asyncio.run(main())
