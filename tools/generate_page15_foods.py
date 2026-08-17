import asyncio,json,re
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"content"/"rehema";VOICE="sw-TZ-RehemaNeural";AUDIO="page-015-foods-v18.mp3";VERSION=18
segments=[
 ("Vyakula vinavyoliwa mchana.",1),
 ("Picha ya vyakula vya mchana inaonesha samaki, maharage, ndizi, maembe, nanasi, papai, mboga za majani, ugali na glasi ya maziwa.","image"),
 ("Vyakula vinavyoliwa jioni.",2),
 ("Picha ya vyakula vya jioni inaonesha njegere, wali, kuku, mtindi, mboga za majani, karoti, bilinganya, samaki, maharage, glasi ya maziwa, nanasi, ndizi, maembe na papai.","image"),
 ("Zoezi la Kwanza.",3),
 ("Moja. Taja vyakula unavyokula asubuhi, mchana na jioni.",4),
 ("Mbili. Eleza ni kwa nini tunakula chakula.",6),
 ("Tatu. Chora au bainisha vyakula unavyopenda kula.",8),
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
 entry={"audio":AUDIO,"voice":VOICE,"version":VERSION,"words":cues};(OUT/"page-015.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8")
 p=OUT/"timecodes.json";data=json.loads(p.read_text(encoding="utf-8"));data["15"]=entry;p.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
 print(f"audio={AUDIO} words={len(cues)}")
asyncio.run(main())
