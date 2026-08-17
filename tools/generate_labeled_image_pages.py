import asyncio, html, json, re, sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "content" / "rehema"
VOICE = "sw-TZ-RehemaNeural"
VERSION = 33

# These transcript rows are captions/numbers extracted from the picture layout.
# They are replaced by the clean, correctly ordered labels below so that the
# voice does not read a jumbled caption before describing the picture.
SKIP_NODES = {
    22: {20, 21, 22},
    24: {13, 14, 15, 16},
    25: set(range(2, 9)),
    26: {1, 2, 3},
    27: set(),
    28: {2, 3, 4, 5, 6},
    29: {2, 3, 4, 5, 6, 7},
    31: {22},
    32: {3, 4, 6, 7},
    33: {1, 2, 3, 4},
    35: {3, 4, 5},
    41: {1, 2},
    34: {29, 30, 31},
    42: {3},
    43: set(),
    44: set(),
    48: set(),
    49: set(),
    45: {5, 6, 7, 8, 9, 10},
    51: set(), 52: set(), 53: set(),
    57: set(range(1, 12)),
    59: {1, 2, 3, 4, 5},
    60: {3, 4, 5, 6},
    63: {1, 2, 3, 4},
    67: set(range(3, 15)),
    68: set(),
}

LABELS = {
    22: [
        "Picha namba moja. Mchezo wa mpira wa mguu. Picha inaonesha watoto wakicheza mpira wa mguu uwanjani, huku watoto wengine wakitazama.",
        "Picha namba mbili. Mchezo wa mdako. Picha inaonesha watoto wawili wakicheza mdako wakiwa wamekaa chini.",
        "Picha namba tatu. Mchezo wa mpira wa pete. Picha inaonesha watoto wakicheza mpira wa pete, na mtoto mmoja akirusha mpira kuelekea kwenye pete.",
        "Picha namba nne. Mchezo wa dama. Picha inaonesha watoto wakicheza mchezo wa kuruka kwenye visanduku vilivyochorwa ardhini.",
    ],
    24: [
        "Picha namba moja. Picha ya juu inaonesha watoto wawili wakifanya usafi. Upande wa kushoto, mtoto wa kiume ameketi karibu na bomba la maji. Anafua nguo kwa maji na sabuni ndani ya beseni. Upande wa kulia, mtoto wa kike ananawa mikono kwa maji yanayotiririka kutoka kwenye bomba.",
        "Picha namba mbili. Mswaki wa brashi. Picha inaonesha mswaki wenye mpini na brashi ya kusafishia meno.",
        "Picha namba tatu. Mswaki wa mti. Picha inaonesha kijiti cha mti kinachotumika kusafisha meno.",
        "Picha namba nne. Dawa ya meno. Picha inaonesha bomba la dawa ya meno.",
        "Picha namba tano. Maji safi na salama. Picha inaonesha kikombe chenye maji safi ya kusukutua mdomo.",
    ],
    25: [
        "Picha namba moja. Kuweka dawa ya meno kwenye mswaki. Picha inaonesha dawa ya meno ikiwekwa kwenye brashi ya mswaki.",
        "Picha namba mbili a. Kusugua meno. Picha inaonesha mtoto akisugua sehemu ya nje ya meno.",
        "Picha namba mbili b. Kusugua meno. Picha inaonesha mtoto akisugua sehemu nyingine ya meno kwa mswaki.",
        "Picha namba mbili c. Kusugua meno. Picha inaonesha mtoto akiendelea kusugua meno yake kwa utaratibu.",
        "Picha namba tatu. Kusafisha ulimi. Picha inaonesha mtoto akisafisha ulimi kwa mswaki.",
        "Picha namba nne. Kusukutua kwa maji safi na salama. Picha inaonesha mtoto akisukutua mdomo kwa maji safi.",
    ],
    26: [
        "Picha namba tano. Kutema maji yaliyo mdomoni. Picha inaonesha mtoto akitema maji baada ya kusukutua mdomo.",
        "Picha namba sita. Kuosha mswaki. Picha inaonesha mswaki ukioshwa kwa maji safi.",
        "Picha namba saba. Kuhifadhi mswaki. Picha inaonesha mswaki umewekwa mahali safi baada ya kuoshwa.",
        "Kifaa cha kwanza ni beseni. Picha inaonesha beseni la kuwekea maji safi ya kusafishia masikio.",
        "Kifaa cha pili ni kitambaa safi na laini. Picha inaonesha kitambaa kilichokunjwa kinachotumika kusafisha sehemu za nje za masikio.",
        "Kifaa cha tatu ni kioo. Picha inaonesha kioo kinachotumika kukagua kama masikio yamekuwa safi.",
        "Kifaa cha nne ni sabuni. Picha inaonesha kipande cha sabuni kinachotumika pamoja na maji kusafisha kitambaa.",
    ],
    27: [
        "Picha namba moja. Picha inaonesha mtoto akisafisha mikunjo ya mbele ya sikio kwa kitambaa safi na laini.",
        "Picha namba mbili. Picha inaonesha mtoto akisafisha sehemu ya nyuma ya sikio kwa kitambaa safi na laini.",
    ],
    28: [
        "Picha namba moja. Wembe. Picha inaonesha wembe wa kukatia kucha.",
        "Picha namba mbili. Kikata kucha. Picha inaonesha kifaa maalumu cha kukata kucha.",
        "Picha namba tatu. Sabuni. Picha inaonesha kipande cha sabuni ya kunawia mikono.",
        "Picha namba nne. Brashi. Picha inaonesha brashi ya kusafishia kucha.",
        "Picha namba tano. Mkasi. Picha inaonesha mkasi wa kukatia kucha.",
        "Picha namba sita. Beseni. Picha inaonesha beseni la kuwekea maji.",
        "Picha namba saba. Taulo. Picha inaonesha taulo la kukaushia mikono.",
    ],
    29: [
        "Picha namba moja. Kukata kucha kwa kutumia kikata kucha. Picha inaonesha kucha zikikatwa kwa kikata kucha.",
        "Picha namba mbili. Kukata kucha kwa kutumia wembe. Picha inaonesha kucha zikikatwa kwa uangalifu kwa kutumia wembe.",
        "Picha namba tatu. Kusafisha mikono kwa maji na sabuni. Picha inaonesha mikono ikioshwa kwa maji safi na sabuni baada ya kukata kucha.",
    ],
    31: [
        "Picha namba moja. Mtoto mwenye mapunye. Picha inaonesha kichwa cha mtoto kilichonyolewa. Kwenye ngozi ya kichwa kuna mabaka kadhaa yanayoonesha sehemu zilizoathiriwa na ugonjwa wa mapunye.",
    ],
    32: [
        "Picha namba moja. Taulo. Picha inaonesha taulo la kujikaushia baada ya kuoga.",
        "Picha namba mbili. Sabuni. Picha inaonesha sabuni ya kuogea.",
        "Picha namba tatu. Kitambaa. Picha inaonesha kitambaa cha kujisafishia mwili.",
        "Picha namba nne. Dodoki. Picha inaonesha dodoki la kujisugulia mwili.",
        "Picha namba tano. Beseni. Picha inaonesha beseni la kuwekea maji ya kuoga.",
        "Picha namba sita. Kandambili. Picha inaonesha kandambili za kuvaa wakati wa kuoga.",
        "Picha namba saba. Kopo. Picha inaonesha kopo la kuchotea maji.",
        "Picha namba nane. Kuvua nguo. Picha inaonesha mtoto akivua nguo kabla ya kuoga.",
        "Picha namba tisa. Kujimwagia maji. Picha inaonesha mtoto akijimwagia maji mwilini.",
    ],
    33: [
        "Picha namba tatu. Kujipaka sabuni. Picha inaonesha mtoto akijipaka sabuni mwilini.",
        "Picha namba nne. Kujisugua kwa dodoki. Picha inaonesha mtoto akijisugua mwili kwa dodoki.",
        "Picha namba tano. Kujisuuza kwa maji. Picha inaonesha mtoto akijisuuza mwili kwa maji safi.",
        "Picha namba sita. Kujikausha maji kwa taulo. Picha inaonesha mtoto akijikausha mwili kwa taulo.",
    ],
    35: [
        "Picha namba moja. Picha inaonesha nguo za rangi zikitenganishwa na nguo nyeupe kabla ya kufuliwa.",
        "Picha namba mbili. Picha inaonesha nguo zikifuliwa kwa kusuguliwa ndani ya beseni lenye maji na sabuni.",
        "Picha namba tatu. Picha inaonesha nguo zikisuuziwa kwa maji safi baada ya kufuliwa.",
        "Picha namba nne. Picha inaonesha nguo zikikamuliwa ili kuondoa maji.",
    ],
    41: [
        "Picha namba moja. Kuhifadhi vyombo mahali safi. Picha inaonesha kabati lenye milango ya kioo na vyombo safi vilivyopangwa kwenye rafu.",
    ],
    34: [
        "Kifaa cha kwanza ni sabuni ya mche. Picha inaonesha kipande kirefu cha sabuni ya kufulia.",
        "Kifaa cha pili ni sabuni ya unga. Picha inaonesha pakiti ya sabuni ya unga ya kufulia.",
        "Kifaa cha tatu ni beseni la maji. Picha inaonesha beseni linalotumika kufulia nguo.",
        "Kifaa cha nne ni ndoo ya maji. Picha inaonesha ndoo ya kubebea na kuhifadhi maji ya kufulia.",
        "Kifaa cha tano ni vibanio. Picha inaonesha vibanio vinavyotumika kushikilia nguo zinapoanikwa.",
    ],
    42: [
        "Picha namba moja. Picha inaonesha mtoto akikojoa pembeni ya shimo la choo. Hatumii choo kwa usahihi kwa sababu uchafu unaanguka sakafuni.",
        "Picha namba mbili. Picha inaonesha mtoto akikojoa ndani ya shimo la choo kwa kulenga shimo. Mtoto huyu anatumia choo kwa usahihi.",
        "Picha namba tatu. Picha inaonesha mtoto akifunua mfuniko wa shimo la choo kwa kutumia fimbo kabla ya kutumia choo. Karibu kuna ndoo ya maji.",
    ],
    43: [
        "Picha namba moja. Picha inaonesha mtoto akifunika shimo la choo kwa kutumia fimbo baada ya kujisaidia.",
        "Picha namba mbili. Picha inaonesha mtoto akinawa mikono kwa maji yanayotiririka kutoka kwenye bomba baada ya kutumia choo.",
    ],
    44: [
        "Picha namba moja. Picha inaonesha wanafunzi wawili wakisafisha choo. Mwanafunzi mmoja anafagia sakafu, na mwingine anamwaga maji karibu na shimo la choo. Kuna ndoo, ufagio na kifaa cha kusugulia sakafu.",
    ],
    48: [
        "Kifaa cha kwanza ni reki. Reki hutumika kukusanya majani na takataka.",
        "Kifaa cha pili ni ndoo. Ndoo hutumika kubebea maji au takataka.",
        "Kifaa cha tatu ni ufagio. Ufagio hutumika kufagia uchafu.",
        "Kifaa cha nne ni panga. Panga hutumika kukata vichaka na matawi madogo.",
        "Kifaa cha tano ni brashi ya sakafu. Brashi hutumika kusugua sakafu.",
        "Kifaa cha sita ni koleo la takataka. Koleo hutumika kubebea takataka baada ya kufagia.",
        "Kifaa cha saba ni ufagio wa nje. Ufagio huu hutumika kufagia uwanja.",
        "Kifaa cha nane ni mkasi wa bustani. Mkasi hutumika kukata mimea na matawi madogo.",
        "Kifaa cha tisa ni jembe. Jembe hutumika kulimia na kutifua udongo.",
    ],
    49: [
        "Picha namba moja. Picha inaonesha mazingira ya shule yenye wanafunzi wanne wanaofanya usafi. Upande wa kushoto, mwanafunzi anafagia uwanja kwa ufagio mrefu. Katikati, mwanafunzi ameinama akiondoa magugu ardhini. Upande wa kulia, mwanafunzi anakata na kusawazisha ua wa mimea. Mbele yake, mwanafunzi mwingine ameshika fyekeo na anafyeka majani marefu. Nyuma kuna majengo ya shule, miti na bendera. Wanafunzi wanashirikiana kufanya mazingira ya shule yawe safi.",
    ],
    45: [
        "Kifaa cha kwanza ni wembe. Picha inaonesha wembe wenye ncha kali unaotumika kunyolea.",
        "Kifaa cha pili ni mswaki. Picha inaonesha mswaki unaotumika kusafisha meno.",
        "Kifaa cha tatu ni sindano ya kutogea masikio au kushonea nguo. Picha inaonesha sindano yenye uzi.",
        "Kifaa cha nne ni chanuo. Picha inaonesha chanuo lenye meno mapana linalotumika kuchana nywele.",
        "Kifaa cha tano ni kitana. Picha inaonesha kitana chenye meno kinachotumika kuchana nywele.",
        "Kifaa cha sita ni sindano. Picha inaonesha sindano ya hospitali yenye ncha kali.",
        "Kifaa cha saba ni pini. Picha inaonesha pini ya usalama yenye ncha kali.",
    ],
    51: ["Picha namba moja. Picha inaonesha mwalimu na wanafunzi wawili kwenye kitalu. Mwalimu anawaelekeza namna ya kupanda mbegu. Mbele yao kuna mashimo yaliyotayarishwa na miche midogo kwenye viriba."],
    52: [
        "Picha namba moja. Picha inaonesha wanafunzi wawili wakitunza kitalu kilichofunikwa kwa nyasi kavu. Mwanafunzi mmoja anapanga nyasi, na mwingine anamwagilia kitalu kwa kutumia kopo la kumwagilia.",
        "Picha namba mbili. Picha inaonesha wanafunzi wawili wakipanda miche kwenye mashimo yaliyoandaliwa. Karibu yao kuna miche mingine ndani ya viriba.",
    ],
    53: ["Picha namba moja. Picha inaonesha wanafunzi wawili wakimwagilia miche iliyopandwa kwa kutumia makopo ya kumwagilia. Miche imepandwa kwa mistari na inaendelea kukua."],
    57: [
        "Picha namba moja. Simba. Maandishi ya picha yanasema: Mimi ni simba. Ni mfalme wa pori. Binadamu huniogopa. Picha inaonesha simba mwenye manyoya mengi shingoni.",
        "Picha namba mbili. Nge. Maandishi ya picha yanasema: Mimi ni nge. Sumu yangu ni kali. Huwaletea maumivu makali. Picha inaonesha nge mwenye mikono ya kubana na mkia uliopinda.",
        "Picha namba tatu. Mbu. Maandishi ya picha yanasema: Mimi ni mbu. Huwanyonya damu na kuwaletea vijidudu vya malaria. Picha inaonesha mbu mwenye miguu mirefu na mabawa.",
    ],
    59: [
        "Picha namba moja. Alama ya taa za barabarani. Alama ina umbo la pembetatu na ndani kuna taa nyekundu, njano na kijani.",
        "Picha namba mbili. Alama ya watembea kwa miguu. Alama inaonesha mtu anayetembea.",
        "Picha namba tatu. Alama ya kivuko cha wanafunzi. Alama inaonesha watoto wawili wakivuka barabara.",
        "Picha namba nne. Alama ya njia ya waendesha baiskeli. Alama inaonesha baiskeli.",
        "Picha namba tano. Alama ya tahadhari ya kitu kinachoweza kuwaka moto. Alama ina umbo la pembetatu na ndani kuna mchoro wa mwali wa moto.",
    ],
    60: [
        "Picha namba moja. Alama ya hatari ya umeme. Alama ina umbo la pembetatu na ndani kuna mchoro wa radi.",
        "Picha namba mbili. Alama ya njia ya waendesha baiskeli. Alama ina umbo la pembetatu na ndani kuna mchoro wa baiskeli.",
        "Picha namba tatu. Alama ya kivuko cha wanafunzi. Alama ina umbo la pembetatu na ndani kuna watoto wawili wakivuka.",
        "Picha namba nne. Alama ya sumu au hatari ya kifo. Alama ina umbo la pembetatu na ndani kuna fuvu la kichwa na mifupa miwili.",
    ],
    63: [
        "Picha namba tatu inaonesha farasi.", "Picha namba nne inaonesha pundamilia mwenye mistari mwilini.",
        "Picha namba tano inaonesha punda.", "Picha namba sita inaonesha mbwa.",
        "Picha inayofuata inaonesha mamba mwenye mwili mrefu na meno makali.", "Picha inayofuata inaonesha mbuzi.",
        "Picha inayofuata inaonesha twiga mwenye shingo ndefu.", "Picha inayofuata inaonesha ng'ombe mwenye pembe.",
        "Picha ya mwisho inaonesha kiboko mwenye mwili mkubwa.",
    ],
    67: [
        "Kifaa cha kwanza ni kipimajoto.", "Kifaa cha pili ni pini.", "Kifaa cha tatu ni mkasi.",
        "Kifaa cha nne ni glovu.", "Kifaa cha tano ni sindano.", "Kifaa cha sita ni koleo.",
        "Kifaa cha saba ni pamba.", "Kifaa cha nane ni dawa za kutuliza maumivu.",
        "Kifaa cha tisa ni bendeji.", "Kifaa cha kumi ni spiriti.",
        "Picha namba moja inaonesha mtoto akianguka kutoka kwenye mti.",
        "Picha namba mbili inaonesha wanafunzi wawili wakiwa katika hatari karibu na basi linalotembea. Mwanafunzi mmoja ameanguka karibu na gurudumu.",
    ],
    68: [
        "Picha namba tatu inaonesha mtu akikimbia baada ya kuona nyoka ardhini.",
        "Picha namba nne inaonesha mwanafunzi aliyeanguka karibu na pikipiki inayopita.",
        "Picha namba moja ya kutoa taarifa inaonesha wanafunzi watatu wakimsaidia mwenzao aliyeumia mguu. Mmoja anamfunga jeraha kwa kitambaa.",
        "Picha namba mbili ya kutoa taarifa inaonesha mwanafunzi akikimbia kuelekea kwa mtu mzima ili kutoa taarifa kuhusu ajali.",
    ],
}


def transcript(page):
    raw = (ROOT / f"pg{page:03d}_sec001.html").read_text(encoding="utf-8")
    block = re.search(r'<div class="accessible-transcript[^>]*>(.*?)</div>', raw, re.S).group(1)
    nodes = []
    for position, (_, text) in enumerate(re.findall(r'data-id="([^"]+)"[^>]*>(.*?)</span>', block, re.S), 1):
        clean = html.unescape(re.sub(r"<[^>]+>", "", text)).strip()
        if page == 25 and position == 1:
            clean = "Hatua za kusafisha kinywa."
        if page == 26 and clean == "Zoezi la 1":
            clean = "Zoezi la kwanza."
        exercise_names = {"1": "kwanza", "2": "pili", "3": "tatu", "4": "nne", "5": "tano", "6": "sita", "7": "saba", "8": "nane", "9": "tisa", "10": "kumi", "11": "kumi na moja"}
        match = re.fullmatch(r"Zoezi la (\d+)", clean)
        if match and match.group(1) in exercise_names:
            clean = f"Zoezi la {exercise_names[match.group(1)]}."
        if position in SKIP_NODES.get(page, set()):
            continue
        if clean and not re.search(r"AFYA NA MAZINGIRA|\d{2}/\d{2}/\d{4}", clean):
            nodes.append(clean)
    while nodes and re.fullmatch(r"\d+", nodes[-1]):
        nodes.pop()
    return nodes


async def generate(page, semaphore):
    source = [(text, "source", index) for index, text in enumerate(transcript(page), 1)]
    images = [(text, "image", None) for text in LABELS[page]]
    if page == 24:
        body_heading = next((i for i, item in enumerate(source) if item[0] == "Usafi wa mwili"), 9)
        segments = source[:body_heading + 1] + images[:1] + source[body_heading + 1:] + images[1:]
    elif page == 26:
        equipment = next((i for i, item in enumerate(source) if item[0] == "Vifaa"), len(source) - 1)
        segments = images[:3] + source[:equipment + 1] + images[3:] + source[equipment + 1:]
    elif page == 27:
        heading = next((i for i, item in enumerate(source) if item[0] == "Vitendo vya kusafisha masikio"), 8)
        segments = source[:heading + 1] + images + source[heading + 1:]
    elif page in {33, 41}:
        segments = images + source
    elif page in {28, 29}:
        segments = source[:1] + images + source[1:]
    elif page == 31:
        split = next((i for i, item in enumerate(source) if item[0].startswith("Zoezi la ")), len(source))
        segments = source[:split] + images + source[split:]
    elif page == 32:
        split = next((i for i, item in enumerate(source) if item[0].startswith("Hatua za kuoga")), len(source))
        segments = source[:split] + images[:7] + source[split:split + 1] + images[7:] + source[split + 1:]
    elif page == 35:
        segments = source[:2] + images + source[2:]
    elif page == 34:
        heading = next((i for i, item in enumerate(source) if item[0] == "Vifaa vya kufulia nguo"), len(source) - 1)
        segments = source[:heading + 1] + images + source[heading + 1:]
    elif page == 42:
        question = next((i for i, item in enumerate(source) if item[0].startswith("Picha ya mtoto")), 1)
        steps = next((i for i, item in enumerate(source) if item[0] == "Hatua sahihi za matumizi ya choo"), len(source) - 1)
        segments = source[:question + 1] + images[:2] + source[question + 1:steps + 1] + images[2:] + source[steps + 1:]
    elif page == 43:
        fifth = next((i for i, item in enumerate(source) if item[0] == "5."), len(source))
        segments = source[:fifth] + images[:1] + source[fifth:] + images[1:]
    elif page == 44:
        segments = source[:1] + images + source[1:]
    elif page == 48:
        segments = source + images
    elif page == 49:
        questions = next((i for i, item in enumerate(source) if item[0] == "Maswali"), len(source))
        segments = source[:questions] + images + source[questions:]
    elif page == 45:
        heading = next((i for i, item in enumerate(source) if item[0] == "Vifaa vinavyochangia maambukizi ya VVU"), 3)
        segments = source[:heading + 1] + images + source[heading + 1:]
    elif page == 51:
        heading = next((i for i, item in enumerate(source) if item[0] == "Kanuni za upandaji wa mbegu"), len(source))
        segments = source[:heading] + images + source[heading:]
    elif page == 52:
        step_six = next((i for i, item in enumerate(source) if item[0] == "6."), len(source))
        segments = source[:step_six] + images[:1] + source[step_six:] + images[1:]
    elif page == 53:
        questions = next((i for i, item in enumerate(source) if item[0] == "Maswali"), len(source))
        segments = source[:questions] + images + source[questions:]
    elif page == 57:
        segments = images + source
    elif page == 59:
        segments = images[:4] + source + images[4:]
    elif page == 60:
        segments = source[:2] + images + source[2:]
    elif page == 63:
        heading = next((i for i, item in enumerate(source) if item[0].startswith("Jadili na wenzako")), len(source))
        segments = images[:4] + source[:heading + 1] + images[4:] + source[heading + 1:]
    elif page == 67:
        accidents = next((i for i, item in enumerate(source) if item[0].startswith("Ajali zinazoweza")), len(source))
        segments = source[:2] + images[:10] + source[2:] + images[10:]
    elif page == 68:
        segments = images[:2] + source + images[2:]
    else:
        segments = source + images
    text = " ".join(segment[0] for segment in segments)
    cues = []
    audio_name = f"page-{page:03d}-labeled-v33.mp3"
    async with semaphore:
        stream = edge_tts.Communicate(text, VOICE, rate="-8%", boundary="WordBoundary")
        with (OUT / audio_name).open("wb") as audio:
            async for event in stream.stream():
                if event["type"] == "audio":
                    audio.write(event["data"])
                elif event["type"] == "WordBoundary":
                    start = event["offset"] / 10_000_000
                    duration = event["duration"] / 10_000_000
                    cues.append({"text": event["text"], "start": round(start, 6), "end": round(start + duration, 6)})
    cursor = 0
    for sentence, kind, index in segments:
        count = len(re.findall(r"\S+", sentence))
        for cue in cues[cursor:cursor + count]:
            if kind == "image":
                cue["targetImage"] = True
            else:
                cue["sourceIndex"] = index
        cursor += count
    entry = {"audio": audio_name, "voice": VOICE, "version": VERSION, "words": cues}
    (OUT / f"page-{page:03d}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(page), entry


async def main():
    pages = [int(value) for value in sys.argv[1:]] if len(sys.argv) > 1 else list(LABELS)
    semaphore = asyncio.Semaphore(3)
    results = await asyncio.gather(*(generate(page, semaphore) for page in pages))
    path = OUT / "timecodes.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for page, entry in results:
        data[page] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("generated", ", ".join(page for page, _ in results))


asyncio.run(main())
