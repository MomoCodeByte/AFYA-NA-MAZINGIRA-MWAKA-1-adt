import asyncio,json,re
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"content"/"rehema";VOICE="sw-TZ-RehemaNeural";AUDIO="page-019-harms-v18.mp3";VERSION=18
segments=[
 ("Madhara ya kunywa maji yasiyo salama.",1),("Wimbo.",2),
 ("Moja. Usinywe maji yasiyo salama, utaumwa tumbo. Rudia mstari huu mara mbili.",3),("Mbili. Usinywe maji yasiyo salama, utatapika. Rudia mstari huu mara mbili.",5),("Tatu. Usinywe maji yasiyo salama, utaharisha. Rudia mstari huu mara mbili.",7),
 ("Madhara ya kunywa maji yasiyo salama.",9),
 ("Picha namba moja. Kunywa maji yasiyo salama.","image"),("Picha inaonesha mwanamke akichota na kunywa maji moja kwa moja kutoka kwenye mkondo wa maji ulio wazi. Maji hayo yanaweza kuwa na uchafu na vijidudu.","image"),
 ("Picha namba mbili. Kuumwa tumbo.","image"),("Picha inaonesha mwanamke amesimama huku akishika tumbo kwa mikono. Uso wake unaonesha kuwa ana maumivu ya tumbo.","image"),
 ("Picha namba tatu. Kuharisha.","image"),("Picha inaonesha mwanamke akikimbilia kwenye choo huku akishika sehemu ya nyuma ya mwili. Anaonekana kuwa na tatizo la kuharisha.","image"),
 ("Picha namba nne. Kutapika.","image"),("Picha inaonesha mwanamke akiwa ameinama ndani ya choo na anatapika.","image"),
 ("Zoezi la Tatu.",10),("Moja. Taja vyanzo vitatu vya maji.",11),("Mbili. Unywaji wa maji yasiyo safi na salama husababisha nini? A. Nafasi ya jibu. B. Nafasi ya jibu. C. Nafasi ya jibu.",13),
]
async def main():
 text=" ".join(x[0] for x in segments);cues=[]
 with (OUT/AUDIO).open("wb") as audio:
  stream=edge_tts.Communicate(text,VOICE,rate="-8%",boundary="WordBoundary")
  async for event in stream.stream():
   if event["type"]=="audio":audio.write(event["data"])
   elif event["type"]=="WordBoundary":s=event["offset"]/10_000_000;d=event["duration"]/10_000_000;cues.append({"text":event["text"],"start":round(s,6),"end":round(s+d,6)})
 cursor=0
 for sentence,target in segments:
  count=len(re.findall(r"\S+",sentence))
  for cue in cues[cursor:cursor+count]:
   if target=="image":cue["targetImage"]=True
   else:cue["sourceIndex"]=target
  cursor+=count
 entry={"audio":AUDIO,"voice":VOICE,"version":VERSION,"words":cues};(OUT/"page-019.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8")
 p=OUT/"timecodes.json";data=json.loads(p.read_text(encoding="utf-8"));data["19"]=entry;p.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8");print(f"audio={AUDIO} words={len(cues)}")
asyncio.run(main())
