import asyncio,json,re
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"content"/"rehema";VOICE="sw-TZ-RehemaNeural";AUDIO="page-021-fruit-v19.mp3";VERSION=19
segments=[
 ("Madhara ya kula matunda bila kusafisha.",1),
 ("Namba moja. Picha inaonesha mtoto akiinama na kuokota tunda lililoanguka chini ya mti.","image"),
 ("Namba mbili. Picha inaonesha mtoto akila tunda alilookota bila kulisafisha.","image"),
 ("Namba tatu. Picha inaonesha mtoto akishika tumbo kwa mikono na uso wake unaonesha maumivu.","image"),
 ("Namba nne. Picha inaonesha mtoto akikimbilia kwenye choo baada ya kuumwa tumbo.","image"),
 ("Namba tano. Picha inaonesha mtoto akiwa ameinama ndani ya choo na anatapika.","image"),
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
 entry={"audio":AUDIO,"voice":VOICE,"version":VERSION,"words":cues};(OUT/"page-021.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8")
 p=OUT/"timecodes.json";data=json.loads(p.read_text(encoding="utf-8"));data["21"]=entry;p.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8");print(f"audio={AUDIO} words={len(cues)}")
asyncio.run(main())
