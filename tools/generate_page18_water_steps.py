import asyncio,json,re
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"content"/"rehema";VOICE="sw-TZ-RehemaNeural";AUDIO="page-018-water-v19.mp3";VERSION=19
segments=[
 ("Tatu. Eleza sababu ya kutunza chakula kwa kukining'iniza.",1),("Nne. Orodhesha vifaa vinavyotumika kutunza chakula.",3),("Tano. Taja njia nyingine mbili za kutunza chakula.",5),
 ("Maji safi na salama.",7),("Maji ni muhimu katika maisha. Unaweza kupata maji kutoka sehemu mbalimbali. Sehemu hizo ni kama mito, mabomba na visima.",8),("Hatua za kupata maji safi na salama.",13),
 ("Picha namba moja. Kuchemsha maji.","image"),("Picha inaonesha sufuria yenye kifuniko juu ya jiko. Moto unachemsha maji na mvuke unatoka juu ya sufuria.","image"),
 ("Picha namba mbili. Maji yanapoa.","image"),("Picha inaonesha sufuria iliyofunikwa na kuwekwa sehemu salama ili maji yaliyochemshwa yapoe bila kupata uchafu.","image"),
 ("Picha namba tatu. Kuchuja maji.","image"),("Picha inaonesha mwanamke akimimina maji kupitia kitambaa safi kilichowekwa juu ya chombo. Kitambaa kinazuia uchafu kuingia kwenye maji.","image"),
 ("Picha namba nne. Kuhifadhi maji kwenye chombo safi.","image"),("Picha inaonesha ndoo safi yenye mfuniko. Maji yanahifadhiwa ndani na mfuniko unazuia vumbi na uchafu kuingia.","image"),
 ("Picha namba tano. Kunywa maji safi na salama.","image"),("Picha inaonesha mwanamke akinywa maji kwa kutumia glasi safi.","image"),
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
 entry={"audio":AUDIO,"voice":VOICE,"version":VERSION,"words":cues};(OUT/"page-018.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8")
 p=OUT/"timecodes.json";data=json.loads(p.read_text(encoding="utf-8"));data["18"]=entry;p.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8");print(f"audio={AUDIO} words={len(cues)}")
asyncio.run(main())
