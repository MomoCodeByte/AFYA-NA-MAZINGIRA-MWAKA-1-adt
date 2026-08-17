import asyncio,json,re
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"content"/"rehema";VOICE="sw-TZ-RehemaNeural";AUDIO="page-020-fruit-v19.mp3";VERSION=19
segments=[
 ("Faida ya kula matunda yaliyosafishwa.",1),("Hatua za kusafisha matunda.",2),
 ("Namba moja. Maandishi ya picha. Kuokota tunda.","image"),("Maelezo ya picha. Picha inaonesha mtoto akiinama na kuokota tunda lililoanguka chini ya mti.","image"),
 ("Namba mbili. Maandishi ya picha. Kuandaa vifaa vya kusafishia tunda. Maji safi na salama, bakuli na kikombe.","image"),("Maelezo ya picha. Picha inaonesha mtoto akiandaa maji safi kwenye kikombe na bakuli kwa ajili ya kusafisha tunda.","image"),
 ("Namba tatu. Maandishi ya picha. Kusafisha tunda.","image"),("Maelezo ya picha. Picha inaonesha mtoto akiweka matunda ndani ya bakuli na kuyamwagia maji safi ili kuondoa uchafu.","image"),
 ("Namba nne. Maandishi ya picha. Kula tunda lililosafishwa.","image"),("Maelezo ya picha. Picha inaonesha mtoto akila tunda lililosafishwa.","image"),
 ("Namba tano. Maandishi ya picha. Kuwa na afya njema na kucheza kwa furaha.","image"),("Maelezo ya picha. Picha inaonesha watoto wawili wenye afya wakiruka kamba na kucheza kwa furaha.","image"),
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
 entry={"audio":AUDIO,"voice":VOICE,"version":VERSION,"words":cues};(OUT/"page-020.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8")
 p=OUT/"timecodes.json";data=json.loads(p.read_text(encoding="utf-8"));data["20"]=entry;p.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8");print(f"audio={AUDIO} words={len(cues)}")
asyncio.run(main())
