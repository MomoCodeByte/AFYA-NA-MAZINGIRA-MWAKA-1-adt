import asyncio, html, json, re
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
PAGES = [9, 12, 17, 19, 26, 27, 31, 35, 36, 37, 64, 67, 71]
NUMBER_WORDS = {str(i): word for i, word in enumerate(["Sifuri", "Moja", "Mbili", "Tatu", "Nne", "Tano", "Sita", "Saba", "Nane", "Tisa", "Kumi"], 0)}

CONFIG = {
    8: {"replace": {"pg008_n0002": "Angalia na bainisha picha hii, kisha jibu swali.", "pg008_n0005": "Chora au chunguza mwili wa binadamu na uoneshe sehemu za nje za mwili"}, "remove": {"pg008_n0006"}, "patch": {"pg008_n0002": 0, "pg008_n0005": 1}, "after": {"pg008_n0002": ["Picha inaonesha mtoto wa kiume akiwa amesimama na kunyoosha mikono. Mistari inaelekeza kichwa, macho, masikio, pua, mdomo, mikono, vidole, tumbo, miguu na nyayo."]}},
    9: {"replace": {"pg009_n0008": "Zoezi la Kwanza"}, "after": {"pg009_n0009": ["Katika swali la kwanza, umbo namba 1 ni mraba wa rangi ya bluu. Umbo namba 2 ni pembetatu ya rangi nyekundu. Umbo namba 3 ni duara la rangi ya kijani. Umbo namba 4 ni mstatili wa rangi ya waridi. Umbo namba 5 ni mcheduara wa rangi ya njano."]}},
    12: {"replace": {"pg012_n0012": "Andika au bainisha vitu vitatu vinavyotoa harufu mbaya.", "pg012_n0014": "Andika au bainisha vitu vinne vinavyotoa harufu nzuri.", "pg012_n0015": "Zoezi la Tatu"}, "patch": {"pg012_n0012": 0, "pg012_n0014": 1}},
    17: {"replace": {"pg017_n0005": "Andika au bainisha vifaa mnavyotumia nyumbani kwenu kutunzia chakula.", "pg017_n0009": "Zoezi la Pili", "pg017_n0011": "Orodhesha au bainisha mifano miwili ya magonjwa yanayotokana na kula chakula kisichotunzwa vizuri."}, "remove": {"pg017_n0006", "pg017_n0012"}, "patch": {"pg017_n0005": 0, "pg017_n0011": 1}},
    19: {"replace": {"pg019_n0010": "Zoezi la Tatu"}},
    26: {"replace": {"pg026_n0004": "Zoezi la Kwanza"}},
    27: {"replace": {"pg027_n0012": "Zoezi la Pili"}},
    31: {"replace": {"pg031_n0023": "Zoezi la Nne", "pg031_n0025": "Andika au bainisha faida nne za kunyoa nywele."}, "patch": {"pg031_n0025": 0}},
    35: {"replace": {"pg035_n0002": "Angalia na bainisha picha namba 1 hadi 5, kisha fanya zoezi la Sita."}, "patch": {"pg035_n0002": 0}, "after": {"pg035_n0005": ["Picha namba 1 inaonesha mtoto akitenganisha nguo nyeupe na nguo za rangi. Picha namba 2 inaonesha mtoto akifikicha nguo kwa sabuni ndani ya beseni. Picha namba 3 inaonesha mtoto akisuuza nguo kwa maji safi. Picha namba 4 inaonesha mtoto akikamua nguo ili kuondoa maji."]}},
    36: {"replace": {"pg036_n0002": "Zoezi la Sita", "pg036_n0003": "Panga na bainisha sentensi kwa mtiririko wa matukio katika picha."}, "patch": {"pg036_n0003": 0}, "after": {"pg036_n0001": ["Picha namba 5 inaonesha mtoto akianika nguo kwenye kamba na kuzibana kwa vibanio ili zikauke."]}},
    37: {"replace": {"pg037_n0001": "Zoezi la Saba", "pg037_n0003": "Andika au bainisha sababu tatu za kufua nguo."}, "patch": {"pg037_n0003": 0}},
    64: {"replace": {"pg064_n0001": "Zoezi la Kwanza"}},
    41: {"replace": {"pg041_n0010": "Andika au bainisha majina ya vyombo ulivyowahi kuviosha."}, "patch": {"pg041_n0010": 0}},
    49: {"replace": {"pg049_n0011": "Tazama na bainisha picha hii kisha jibu maswali."}, "patch": {"pg049_n0011": 0}, "after": {"pg049_n0011": ["Picha inaonesha wanafunzi wakisafisha mazingira ya shule. Kijana wa kiume anafagia njia kwa ufagio. Kijana wa kike anakusanya majani kwa reki. Kijana mwingine wa kike anatunza kichaka, na kijana wa kiume anabeba matawi yaliyokusanywa."]}},
    50: {
        "replace": {"pg050_n0001": "Zoezi la Kwanza"},
        "remove": {"pg050_n0005", "pg050_n0006", "pg050_n0007", "pg050_n0008", "pg050_n0009", "pg050_n0010", "pg050_n0011"},
        "after": {"pg050_n0004": [
            "Huondoa vumbi na uchafu.",
            "Jina la kifaa hiki ni fagio. Fagio hutumika kuondoa vumbi na uchafu kwa kufagia na kusukuma takataka.",
            "Hutumika kulimia.",
            "Jina la kifaa hiki ni jembe. Jembe hutumika kulimia na kutifua udongo.",
            "Hutumika kukusanya nyasi na takataka.",
            "Jina la kifaa hiki ni reki. Reki hutumika kukusanya nyasi, majani na takataka.",
            "Hutumika kuhifadhi takataka kabla ya kuzitupa shimoni.",
            "Jina la kifaa hiki ni pipa la takataka. Pipa hutumika kuhifadhi takataka kabla ya kuzitupa shimoni.",
            "Hutumika kukatia maua.",
            "Jina la kifaa hiki ni mkasi. Mkasi hutumika kukatia maua na sehemu nyingine za mimea.",
            "Hubebea takataka baada ya kufagia.",
            "Jina la kifaa hiki ni koleo la takataka. Koleo la takataka hutumika kubebea takataka baada ya kufagia."
        ]}
    },
    54: {
        "remove": {"pg054_n0002", "pg054_n0003", "pg054_n0004"},
        "after": {"pg054_n0001": [
            "Picha ya kwanza. Picha inaonesha watoto wawili karibu na nyumba. Kuna vipande vya chupa na takataka zenye ncha kali chini. Mtoto mmoja ameinua mguu baada ya kukanyaga sehemu yenye uchafu huo. Hatari iliyopo ni kukatwa au kuchomwa na vipande vyenye ncha kali. Hali hii inaweza kusababisha jeraha, kutokwa damu au maambukizi. Ili kujikinga, vaa viatu na usicheze mahali penye vioo vilivyovunjika au takataka.",
            "Picha ya pili. Picha inaonesha sehemu yenye maji mengi iliyozungukwa na miamba. Kuna watoto wawili ndani ya maji. Mtoto mmoja amenyoosha mikono juu huku akihangaika ndani ya maji. Hatari iliyopo ni kuzama. Hali hii inaweza kusababisha kuumia, kupoteza fahamu au kifo. Ili kujikinga, watoto wasiingie kwenye maji mengi bila uangalizi wa mtu mzima na vifaa vya usalama.",
            "Picha ya tatu. Picha inaonesha mtoto ameketi sakafuni karibu na kifaa cha umeme. Kuna kifaa cha umeme kinachotoa cheche na chombo chenye ncha kali sakafuni. Mtoto anashika sehemu ya umeme inayotoa cheche. Hatari iliyopo ni kunaswa au kuungua na umeme. Hali hii inaweza kusababisha majeraha makubwa, kuungua au kifo. Ili kujikinga, watoto wasiguse nyaya, soketi au vifaa vya umeme. Tatizo la umeme lishughulikiwe na mtu mzima mwenye ujuzi.",
            "Picha ya nne. Picha inaonesha mkondo wa maji wenye kingo zenye mteremko na mawe. Kuna mtoto na sehemu nyembamba iliyowekwa juu ya maji. Mtoto anavuka mkondo wa maji kwa kutumia sehemu hiyo nyembamba. Hatari iliyopo ni kuteleza na kuanguka ndani ya maji. Hali hii inaweza kusababisha kuumia au kuzama. Ili kujikinga, tumia daraja salama na usivuke mkondo wa maji kwenye sehemu nyembamba au inayoteleza.",
            "Ni hatari gani umeisikia katika kila picha? Unaweza kufanya nini ili kujikinga?"
        ]}
    },
    55: {
        "remove": {"pg055_n0008", "pg055_n0009"},
        "after": {"pg055_n0007": [
            "Picha ya kwanza. Picha inaonesha njia karibu na nyumba. Kuna mtoto anayebeba kikapu kikubwa chenye vitu vingi kichwani. Mtoto anatembea huku akiushikilia mzigo huo kwa mikono. Hatari iliyopo ni kubeba mzigo mzito usiolingana na uwezo wa mtoto. Hali hii inaweza kusababisha kuanguka, kuumia kichwa au mgongo. Ili kujikinga, mtoto asibebe mzigo mzito na aombe msaada wa mtu mzima.",
            "Picha ya pili. Picha inaonesha chumba chenye mlango, meza, sahani na pipa. Kuna mtoto aliyejificha chini ya meza, akiwa na kifaa kidogo kinachowaka karibu na uso na boksi dogo sakafuni. Mtoto anashika kifaa hicho karibu na mdomo. Hatari iliyopo ni moto na moshi ndani ya chumba. Hali hii inaweza kusababisha kuungua, kuathiri afya au kuwasha moto. Ili kujikinga, watoto wasichezee moto, viberiti au vitu vinavyowaka.",
            "Picha ya tatu. Picha inaonesha njia karibu na nyumba. Kuna mtu mzima mwenye begi na mtoto aliyevaa sare ya shule na kubeba mkoba. Mtu mzima ananyoosha mkono kumpa mtoto kitu, huku mtoto akiendelea kutembea na kuinua mkono kukataa. Hatari iliyopo ni mtoto kushawishiwa kupokea kitu au kuondoka na mtu asiyemfahamu. Hali hii inaweza kumweka mtoto katika mazingira yasiyo salama. Ili kujikinga, usipokee vitu wala kuandamana na mtu usiyemfahamu, na toa taarifa kwa mtu mzima unayemwamini.",
            "Picha ya nne. Picha inaonesha barabara yenye gari linalokaribia. Kuna watoto watatu na mpira mbele ya gari. Watoto wanacheza mpira katikati ya barabara huku gari likiwa karibu nao. Hatari iliyopo ni kugongwa na gari. Hali hii inaweza kusababisha majeraha makubwa au kifo. Ili kujikinga, watoto wacheze mpira uwanjani na si barabarani.",
            "Ni kitendo gani hatarishi ulichosikia katika kila picha? Unaweza kufanya nini ili kujikinga?"
        ]}
    },
    67: {
        "replace": {"pg067_n0015": "Zoezi la Kwanza"},
        "after": {"pg067_n0023": [
            "Picha ya kwanza. Picha inaonesha eneo la nje lenye mti na njia. Kuna mtoto anayeanguka kutoka kwenye tawi la mti. Hatari iliyopo ni kupanda juu ya mti na kuanguka. Hali hii inaweza kusababisha michubuko, kuvunjika mfupa au kuumia kichwa. Ili kujikinga, watoto wasipande miti mirefu na wacheze katika sehemu salama.",
            "Picha ya pili. Picha inaonesha barabara yenye basi. Kuna wanafunzi wawili karibu na basi, na mwanafunzi mmoja anaanguka karibu na gurudumu. Hatari iliyopo ni kukimbia au kucheza karibu na gari linalotembea. Hali hii inaweza kusababisha kugongwa, majeraha makubwa au kifo. Ili kujikinga, simama mbali na gari, vuka barabara kwa uangalifu na fuata maelekezo ya usalama.",
            "Ni ajali gani imeonekana katika kila picha? Unaweza kufanya nini ili kuepuka ajali hizo?"
        ]}
    },
    68: {
        "after": {"pg068_n0002": [
            "Picha ya tatu. Picha inaonesha eneo la nje lenye nyasi na njia. Kuna mtoto na nyoka wawili ardhini. Mtoto anakimbia kuwaepuka nyoka. Hatari iliyopo ni kuumwa na nyoka. Hali hii inaweza kusababisha maumivu, sumu kuingia mwilini au kifo. Ili kujikinga, usiwakaribie nyoka na toa taarifa kwa mtu mzima unapomwona nyoka.",
            "Picha ya nne. Picha inaonesha barabara. Kuna mtoto, pikipiki na mwendesha pikipiki. Pikipiki inamgonga mtoto na mtoto anaanguka karibu na gurudumu la mbele. Hatari iliyopo ni kugongwa na pikipiki. Hali hii inaweza kusababisha majeraha makubwa au kifo. Ili kujikinga, vuka barabara kwa uangalifu katika sehemu salama na uangalie magari kabla ya kuvuka.",
            "Picha ya kwanza katika kutoa taarifa ya ajali. Picha inaonesha eneo la shule lenye nyasi. Kuna wanafunzi wanne. Mwanafunzi mmoja ameketi chini akiwa ameumia mguu, huku wenzake watatu wakimsaidia. Hatari iliyopo ni jeraha kutopata msaada kwa wakati. Hali hii inaweza kuongeza maumivu au kufanya jeraha kuwa kubwa zaidi. Ili kujikinga, usimsogeze aliyeumia bila uangalifu na mwite mtu mzima atoe huduma.",
            "Picha ya pili katika kutoa taarifa ya ajali. Picha inaonesha njia iliyo mbele ya jengo. Kuna mwanafunzi anayekimbia na mtu mzima aliyesimama mlangoni. Mwanafunzi anakimbia kuelekea kwa mtu mzima ili kutoa taarifa ya ajali. Hatari iliyopo ni kuchelewa kutoa taarifa wakati mtu ameumia. Hali hii inaweza kuchelewesha huduma na kuongeza madhara. Ili kujikinga, toa taarifa mara moja kwa mwalimu, mzazi au mtu mzima anayepatikana.",
            "Ni hatari gani iliyotokea katika picha hizi? Utatoa taarifa kwa nani ajali inapotokea?"
        ]}
    },
    69: {
        "replace": {"pg069_n0001": "Picha ya kwanza. Picha inaonesha eneo la nje lenye nyasi. Kuna mtu mzima, wanafunzi wanne na sanduku la huduma ya kwanza. Mwanafunzi mmoja ameketi chini akiwa ameumia mguu, huku mtu mzima na wanafunzi wengine wakisafisha na kufunga jeraha. Hatari iliyopo ni jeraha kupata uchafu au kutotibiwa kwa usahihi. Hali hii inaweza kusababisha maumivu, kutokwa damu au maambukizi. Ili kujikinga, huduma ya kwanza itolewe na mtu mwenye ujuzi kwa kutumia vifaa safi."},
        "after": {"pg069_n0001": [
            "Picha ya pili. Picha inaonesha sehemu yenye bomba la maji. Kuna mwanafunzi anayenawa mikono kwa maji yanayotiririka. Mwanafunzi anasugua mikono yake baada ya kushiriki kutoa msaada. Hatari iliyopo ni vijidudu kubaki mikononi na kusambaa. Hali hii inaweza kusababisha maambukizi. Ili kujikinga, nawa mikono vizuri kwa maji safi na sabuni baada ya kutoa huduma ya kwanza.",
            "Picha ya tatu. Picha inaonesha njia inayoelekea kwenye jengo lenye kibao cha zahanati. Kuna mtu mzima na wanafunzi wanne. Wanafunzi wawili wanamsaidia mwenzao aliyeumia kutembea, huku mtu mzima akiwaandamana nao kwenda zahanati. Hatari iliyopo ni hali ya aliyeumia kuwa mbaya zaidi bila matibabu. Hali hii inaweza kuongeza maumivu au madhara ya jeraha. Ili kujikinga, mpeleke aliyeumia zahanati au hospitalini kupata matibabu.",
            "Ni hatua gani za kumsaidia aliyeumia umeelewa katika picha hizi? Kwa nini ni muhimu kunawa mikono baada ya kutoa huduma ya kwanza?"
        ]}
    },
    70: {
        "remove": {"pg070_n0003"},
        "after": {"pg070_n0002": [
            "Picha ya kwanza. Picha inaonesha eneo la nje lenye nguzo ya umeme na waya ulioanguka. Kuna watoto watatu. Mtoto mmoja ameshika waya na anaonesha dalili za kunaswa na umeme, huku watoto wengine wawili wakishtuka. Hatari iliyopo ni kugusa waya wenye umeme. Hali hii inaweza kusababisha kuungua, majeraha makubwa au kifo. Ili kujikinga, usiguse waya wa umeme na waite watu wazima au wataalamu wa umeme.",
            "Picha ya pili. Picha inaonesha mtoto aliyeanguka karibu na nguzo na waya wa umeme. Kuna mtu anayesukuma waya mbali kwa kutumia kijiti kirefu. Kitendo kinafanyika bila kumgusa aliyeumia kwa mikono. Hatari iliyopo ni msaidizi kunaswa na umeme ikiwa atagusa waya au mwili wa aliyeumia moja kwa moja. Hali hii inaweza kusababisha watu zaidi kuumia au kufa. Ili kujikinga, kata umeme kwanza na msaada utolewe na mtu mzima mwenye ujuzi kwa kutumia kifaa kisichopitisha umeme.",
            "Picha ya tatu. Picha inaonesha eneo lililo mbali kidogo na waya wa umeme. Kuna watoto wawili wanaomshika mtoto aliyeumia kwa mikono na miguu. Watoto wanamwondoa sehemu ya hatari. Hatari iliyopo ni kumsogeza aliyeumia bila uangalifu. Hali hii inaweza kuongeza majeraha. Ili kujikinga, hakikisha umeme umekatwa na pata msaada wa mtu mzima au mtoa huduma kabla ya kumsogeza aliyeumia.",
            "Picha ya nne. Picha inaonesha njia inayoelekea kwenye jengo lenye kibao cha zahanati. Kuna watoto watatu wanaomsaidia mwenzao kutembea. Watoto wanampeleka aliyeumia zahanati kupata matibabu. Hatari iliyopo ni kuchelewa kupata huduma baada ya kunaswa na umeme. Hali hii inaweza kufanya majeraha kuwa makubwa zaidi. Ili kujikinga, mpeleke aliyeumia zahanati au hospitalini mara moja na toa taarifa kwa mtu mzima.",
            "Ni hatua gani salama za kumsaidia mtu aliyenaswa na umeme? Kwa nini hupaswi kumgusa moja kwa moja?"
        ]}
    },
    71: {"replace": {"pg071_n0001": "Zoezi la Pili", "pg071_n0002": "Andika au tunga sentensi nne kwa kufuata mtiririko wa picha."}, "patch": {"pg071_n0002": 0}},
}

def source_data(page):
    raw = (ROOT / f"pg{page:03d}_sec001.html").read_text(encoding="utf-8")
    transcript = re.search(r'<div class="accessible-transcript[^>]*>(.*?)</div>', raw, re.S).group(1)
    nodes = [(i, html.unescape(re.sub(r"<[^>]+>", "", text)).strip()) for i, text in re.findall(r'data-id="([^"]+)"[^>]*>(.*?)</span>', transcript, re.S)]
    while nodes and ("AFYA NA MAZINGIRA" in nodes[-1][1] or (page != 69 and re.fullmatch(r"\d+", nodes[-1][1]))):
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
        for description_index, description in enumerate(config.get("after", {}).get(node_id, [])):
            kind = "source" if page == 50 and description_index % 2 == 0 else "image"
            segments.append((spoken(description), kind, None))
    full_text = " ".join(text for text, _, _ in segments); cues = []; out = ROOT / "content" / "rehema"; audio_name = f"page-{page:03d}-ordered-v14.mp3"
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
    entry = {"audio": audio_name, "voice": VOICE, "version": 14, "words": cues}
    (out / f"page-{page:03d}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8"); entries[str(page)] = entry
    print(f"page={page} words={len(cues)} audio={(out / audio_name).stat().st_size}")

async def main():
    path = ROOT / "content" / "rehema" / "timecodes.json"; entries = json.loads(path.read_text(encoding="utf-8"))
    for page in PAGES: await generate_page(page, entries)
    path.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

if __name__ == "__main__": asyncio.run(main())
