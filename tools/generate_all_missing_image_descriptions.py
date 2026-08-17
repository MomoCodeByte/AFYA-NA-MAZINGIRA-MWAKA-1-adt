import asyncio, html, json, re
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"content"/"rehema"; VOICE="sw-TZ-RehemaNeural"; VERSION=16

DESCRIPTIONS={
7:["Picha inaonesha mtoto wa kike aliyesimama. Ana kichwa, macho, masikio, pua, mdomo, mikono, vidole, tumbo, miguu na nyayo."],
12:["Jedwali lina picha sita za sehemu za mwili. Picha ya kwanza ni macho. Ya pili ni mdomo. Ya tatu ni sikio. Ya nne ni miguu. Ya tano ni mikono. Ya sita ni pua."],
13:["Zoezi lina sehemu sita za mwili na kazi sita. Chagua sehemu ya mwili, kisha chagua kazi inayolingana nayo.","Picha ya kwanza inaonesha macho. Picha ya pili inaonesha mdomo. Picha ya tatu inaonesha sikio. Picha ya nne inaonesha miguu. Picha ya tano inaonesha mikono. Picha ya sita inaonesha pua."],
14:["Picha zinaonesha vyakula mbalimbali vya asubuhi. Kuna matunda, mboga, nafaka, maziwa, mayai, samaki na vyakula vingine."],
15:["Sehemu ya juu ina picha za vyakula vinavyoliwa mchana. Sehemu ya chini ina picha za vyakula vinavyoliwa jioni. Kuna matunda, mboga, nafaka, nyama, samaki na vinywaji."],
16:["Picha zinaonesha njia za kutunza chakula. Kuna kabati la chakula, jokofu na kifaa cha kuning'inizia chakula juu ya ardhi."],
17:["Picha inaonesha kifaa maalumu cha kutunzia chakula kwa kuning'iniza. Kuna ubao wa juu unaoshikiliwa na kamba na vyombo vya chakula vilivyoning'inizwa chini yake."],
18:["Picha zinaonesha hatua za kupata maji salama. Kuna mtu akichemsha maji, akiyapoza, akiyachuja, akiyahifadhi kwenye chombo safi na akinywa maji yaliyohifadhiwa."],
19:["Picha zinaonesha madhara ya kunywa maji yasiyo salama. Kuna mtoto mwenye maumivu ya tumbo, mtoto anayetapika, mtoto anayeharisha na mtoto anayeonekana dhaifu."],
20:["Picha zinaonesha faida za kula matunda yaliyosafishwa. Kuna watoto wakiosha matunda, wakila matunda safi na wakionekana wenye afya."],
21:["Picha zinaonesha madhara ya kula matunda bila kusafisha. Kuna mtoto mwenye maumivu ya tumbo, mtoto anayetapika, mtoto anayeharisha na mtoto anayejisaidia chooni."],
22:["Picha nne zinaonesha mazoezi ya viungo. Kuna mchezo wa mpira wa mguu, mchezo wa mdako, mchezo wa mpira wa pete na mchezo wa dama."],
24:["Picha zinaonesha usafi wa kinywa. Kuna mtoto akisafisha kinywa na mtu mzima akimsaidia mtoto. Vifaa vinavyoonekana ni mswaki, dawa ya meno na maji safi."],
25:["Picha sita zinaonesha hatua za kusafisha kinywa. Mtoto anaweka dawa kwenye mswaki, anasafisha meno, ulimi na sehemu za ndani za kinywa, kisha anasukutua kwa maji safi."],
26:["Picha zinaonesha mwendelezo wa kusafisha kinywa. Kuna mtoto akisafisha meno na ulimi, mtoto akisukutua na vifaa vya mswaki, dawa ya meno, kikombe na maji."],
27:["Picha zinaonesha usafi wa masikio. Kuna watoto wakisafisha sehemu za nje za masikio kwa kitambaa. Vifaa vinavyoonekana ni kitambaa, taulo, beseni na maji safi."],
28:["Picha zinaonesha vifaa vya kusafisha na kukata kucha. Kuna wembe, kikata kucha, sabuni, brashi, mkasi, beseni na taulo."],
29:["Picha zinaonesha hatua za kukata kucha. Kwanza kucha zinakatwa kwa kifaa salama. Kisha mikono inaoshwa kwa maji safi na sabuni."],
31:["Picha inaonesha kichwa cha mtoto chenye sehemu ya ngozi iliyoathiriwa na ugonjwa wa fangasi unaoitwa mba."],
32:["Picha zinaonesha vifaa na hatua za kuoga. Kuna taulo, sabuni, kitambaa, dodoki, beseni, kandambili, ndoo na mtoto akioga."],
33:["Picha nne zinaonesha hatua za kuoga. Mtoto anajipaka maji, anajisugua kwa sabuni na dodoki, anajisafisha kwa maji, kisha anajikausha kwa taulo."],
34:["Picha zinaonesha vifaa vya kufulia nguo. Kuna beseni la maji, ndoo ya maji, sabuni ya unga na vibanio."],
37:["Picha zinaonesha vifaa vya kupigia nguo pasi. Kuna shuka, pasi ya mkaa, pasi ya umeme na meza."],
40:["Picha zinaonesha vifaa na hatua za kuosha vyombo. Kuna sabuni, beseni, ndoo, mtoto akiosha vyombo na kichanja cha kuanikia vyombo."],
41:["Picha inaonesha kabati lenye milango ya kioo. Ndani yake kuna vyombo safi vilivyopangwa kwenye rafu."],
42:["Picha zinaonesha matumizi yasiyo sahihi na sahihi ya choo. Picha ya kwanza inaonesha mtoto akikojoa sakafuni karibu na choo. Picha ya pili inaonesha mtoto akitumia tundu la choo kwa usahihi. Picha ya mwisho inaonesha mtoto akifunika tundu baada ya kutumia choo."],
43:["Picha zinaonesha hatua za kusafisha choo. Kuna mtu akimwaga maji, akisugua sakafu na brashi, akifagia na kunawa mikono baada ya kazi."],
44:["Picha inaonesha wanafunzi wawili wakisafisha choo. Mmoja anafagia sakafu na mwingine anasugua kwa brashi karibu na ndoo ya maji."],
45:["Picha zinaonesha vifaa vinavyoweza kusambaza VVU vikichangiwa. Kuna wembe, mswaki, sindano, kitana, chanuo na pini."],
46:["Ukurasa huu una maswali ya kujikinga na VVU. Hakuna picha mpya inayohitaji kutambuliwa."],
47:["Picha zinaonesha vifaa vya kusafisha mazingira. Kuna ndoo, ufagio, reki, koleo, brashi, pipa la takataka na vifaa vingine vya kukusanyia uchafu."],
48:["Picha inaonesha wanafunzi wakisafisha mazingira ya shule. Wengine wanafagia, wanakusanya majani, wanakata vichaka na kubeba matawi."],
51:["Picha inaonesha kitalu cha miche karibu na nyumba. Kuna watoto na mtu mzima wakitayarisha udongo, kupanda na kumwagilia miche."],
52:["Picha zinaonesha hatua za kuandaa kitalu. Kuna watoto wakitayarisha udongo, wakisia mbegu, wakifunika na kumwagilia kitalu."],
53:["Picha inaonesha wanafunzi wakipanda na kutunza miche shuleni. Wanaandaa mashimo, wanapanda miche na kuimwagilia maji."],
57:["Picha zinaonesha wanyama mbalimbali. Kuna simba, mbwa, buibui na nyoka. Maumbo ya miili yao na idadi ya miguu yanatofautiana."],
59:["Picha zinaonesha alama za usalama barabarani. Kuna alama ya watoto wanaovuka, taa za kuongozea magari, alama ya kuacha njia na alama nyingine za tahadhari."],
63:["Jedwali lina wanyama wa kufugwa na wanyama wa porini. Kuna farasi, pundamilia, mbwa, paka, twiga, ng'ombe, kiboko na wanyama wengine."],
64:["Picha zinaonesha mimea mbalimbali. Kuna mpunga, alizeti, bilinganya na mbuyu."],
66:["Picha inaonesha sanduku jeupe la huduma ya kwanza lenye alama nyekundu ya msalaba juu yake."],
}

def transcript(page):
    raw=(ROOT/f"pg{page:03d}_sec001.html").read_text(encoding="utf-8")
    block=re.search(r'<div class="accessible-transcript[^>]*>(.*?)</div>',raw,re.S).group(1)
    nodes=[]
    for ident,text in re.findall(r'data-id="([^"]+)"[^>]*>(.*?)</span>',block,re.S):
        clean=html.unescape(re.sub(r'<[^>]+>','',text)).strip()
        if clean and not re.search(r'AFYA NA MAZINGIRA|\d{2}/\d{2}/\d{4}',clean): nodes.append((ident,clean))
    while nodes and re.fullmatch(r'\d+',nodes[-1][1]): nodes.pop()
    return nodes

async def generate(page, sem):
    nodes=transcript(page); segments=[]
    if nodes: segments.append((nodes[0][1],"source",1))
    for desc in DESCRIPTIONS[page]: segments.append((desc,"image",None))
    for i,(_,text) in enumerate(nodes[1:],2): segments.append((text,"source",i))
    full=" ".join(x[0] for x in segments); cues=[]; name=f"page-{page:03d}-accessible-v16.mp3"
    async with sem:
        stream=edge_tts.Communicate(full,VOICE,rate="-8%",boundary="WordBoundary")
        with (OUT/name).open("wb") as audio:
            async for event in stream.stream():
                if event["type"]=="audio": audio.write(event["data"])
                elif event["type"]=="WordBoundary":
                    s=event["offset"]/10_000_000; d=event["duration"]/10_000_000
                    cues.append({"text":event["text"],"start":round(s,6),"end":round(s+d,6)})
    cursor=0
    for text,kind,index in segments:
        count=len(re.findall(r'\S+',text))
        for cue in cues[cursor:cursor+count]:
            if kind=="image": cue["targetImage"]=True
            else: cue["sourceIndex"]=index
        cursor+=count
    print(f"page={page} words={len(cues)}")
    return str(page),{"audio":name,"voice":VOICE,"version":VERSION,"words":cues}

async def main():
    sem=asyncio.Semaphore(3); results=await asyncio.gather(*(generate(p,sem) for p in DESCRIPTIONS))
    path=OUT/"timecodes.json"; data=json.loads(path.read_text(encoding="utf-8"))
    for page,entry in results:
        data[page]=entry; (OUT/f"page-{int(page):03d}.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8")
    path.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"completed={len(results)}")

asyncio.run(main())
