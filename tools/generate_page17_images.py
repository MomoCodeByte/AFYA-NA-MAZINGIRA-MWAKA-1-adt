import asyncio,json,re
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"content"/"rehema";VOICE="sw-TZ-RehemaNeural";AUDIO="page-017-images-v18.mp3";VERSION=18
segments=[
 ("Kufunika chakula kwa ungo, kawa au sahani.",1),
 ("Picha inaonesha meza yenye vyakula. Chakula cha kwanza kimefunikwa kwa ungo. Chakula cha pili kimefunikwa kwa kawa. Pembeni kuna chakula kilichofunikwa kwa sahani.","image"),
 ("Kifaa maalumu cha kutunzia chakula kwa kuning'iniza.",2),
 ("Picha inaonesha vyombo vitatu vyenye chakula. Kila chombo kimefungwa kwa kamba na kuning'inizwa kwenye tawi ili chakula kisigusane na sakafu.","image"),
 ("Kazi ya kufanya.",3),
 ("Moja. Andika au bainisha vifaa mnavyotumia nyumbani kwenu kutunzia chakula.",4),
 ("Mbili. Chora au bainisha vifaa hivyo.",7),
 ("Zoezi la Pili.",9),
 ("Moja. Orodhesha au bainisha mifano miwili ya magonjwa yanayotokana na kula chakula kisichotunzwa vizuri.",10),
 ("Mbili. Taja mifano mitatu ya wadudu wanaoleta vijidudu vya maradhi kwenye chakula.",13),
]
async def main():
 text=" ".join(x[0] for x in segments);cues=[]
 with (OUT/AUDIO).open("wb") as audio:
  stream=edge_tts.Communicate(text,VOICE,rate="-8%",boundary="WordBoundary")
  async for event in stream.stream():
   if event["type"]=="audio":audio.write(event["data"])
   elif event["type"]=="WordBoundary":
    s=event["offset"]/10_000_000;d=event["duration"]/10_000_000;cues.append({"text":event["text"],"start":round(s,6),"end":round(s+d,6)})
 cursor=0
 for sentence,target in segments:
  count=len(re.findall(r"\S+",sentence))
  for cue in cues[cursor:cursor+count]:
   if target=="image":cue["targetImage"]=True
   else:cue["sourceIndex"]=target
  cursor+=count
 entry={"audio":AUDIO,"voice":VOICE,"version":VERSION,"words":cues};(OUT/"page-017.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8")
 p=OUT/"timecodes.json";data=json.loads(p.read_text(encoding="utf-8"));data["17"]=entry;p.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
 print(f"audio={AUDIO} words={len(cues)}")
asyncio.run(main())
