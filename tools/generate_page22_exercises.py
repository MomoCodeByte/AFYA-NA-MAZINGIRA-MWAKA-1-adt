import asyncio,json,re
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"content"/"rehema";VOICE="sw-TZ-RehemaNeural";AUDIO="page-022-exercises-v18.mp3";VERSION=18
segments=[
 ("Wimbo.",1),("Moja. Usile tunda bila kuosha, utaumwa tumbo. Rudia mstari huu mara mbili.",2),("Mbili. Usile tunda bila kuosha, utatapika. Rudia mstari huu mara mbili.",4),("Tatu. Usile tunda bila kuosha, utaharisha. Rudia mstari huu mara mbili.",6),
 ("Zoezi la Nne.",8),("Moja. Unatumia vifaa gani katika kuosha matunda?",9),("Mbili. Taja madhara matatu utakayopata ukila tunda bila kuliosha.",11),
 ("Mazoezi ya viungo.",14),("Tunashauriwa kufanya mazoezi ya viungo kila siku. Mazoezi husaidia kujenga na kuimarisha misuli. Hivyo, hufanya mwili kuwa mkakamavu na wenye afya bora.",15),
 ("Mchezo wa mpira wa mguu.",20),("Picha inaonesha watoto wakicheza mpira wa mguu kwenye uwanja wa shule. Wachezaji wanaufuata mpira huku wanafunzi wengine wakitazama.","image"),
 ("Mchezo wa mdako.",20),("Picha inaonesha watoto wawili wakiwa wamekaa chini na kucheza mdako kwa kutumia kitu kidogo kinachorushwa juu.","image"),
 ("Mchezo wa mpira wa pete.",21),("Picha inaonesha watoto wakicheza mpira wa pete. Mchezaji mmoja anaruka kuelekeza mpira kwenye pete huku wengine wakijaribu kuuzuia.","image"),
 ("Mchezo wa dama.",22),("Picha inaonesha watoto wawili karibu na mchoro wa visanduku ardhini. Mtoto mmoja anaruka ndani ya visanduku huku mwenzake akitazama.","image"),
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
 entry={"audio":AUDIO,"voice":VOICE,"version":VERSION,"words":cues};(OUT/"page-022.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8")
 p=OUT/"timecodes.json";data=json.loads(p.read_text(encoding="utf-8"));data["22"]=entry;p.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8");print(f"audio={AUDIO} words={len(cues)}")
asyncio.run(main())
