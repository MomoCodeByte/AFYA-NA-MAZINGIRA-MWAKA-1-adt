import asyncio, html, json, re
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parents[1]; VOICE="sw-TZ-RehemaNeural"
SEGMENTS=[
 ("Zoezi la pili.",None),("Moja. Taja vitendo hatarishi katika mazingira yako.",None),("Mbili. Unawezaje kujiepusha na mazingira hatarishi?",None),("Tatu. Utafanya nini ukimuona rafiki yako anacheza barabarani?",None),("Nne. Ukiogelea kwenye maji marefu utapata madhara gani?",None),("Tano. Kati ya matendo yafuatayo ni yapi hatarishi?",None),("a. Kupanda juu ya miti mirefu. b. Kusaidia kazi za nyumbani. c. Kucheza sehemu zenye giza. d. Kufagia uwanja. e. Kuchezea wembe au kisu na vitu vyenye ncha kali.",None),("Sita.",None),("Andika, bainisha au eleza tabia hatarishi unazozifahamu.",0),("Viumbe hatarishi katika mazingira.",None),("Vipo viumbe mbalimbali hatarishi katika mazingira yetu. Viumbe hivyo ni kama vile nyoka, nyuki na mbu. Wengine ni tandu, simba, chatu, chui na fisi.",None),("Kazi ya kufanya. Kujigamba.",None),("Mimi ni Swila. Nina sumu kali, ikikupata itakuua.",None),("Mimi ni chatu. Nina uwezo wa kumeza binadamu.",None)]
TEXT=" ".join(t for t,_ in SEGMENTS)
def norm(v):
 v=re.sub(r"[^a-z0-9\u00c0-\u024f]+","",v.lower());return {"moja":"1","mbili":"2","pili":"2","tatu":"3","nne":"4","tano":"5","sita":"6"}.get(v,v)
def words():
 raw=(ROOT/"pg056_sec001.html").read_text(encoding="utf-8");f=re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>',raw,re.S);return [(int(i),html.unescape(re.sub(r"<[^>]+>","",t)).strip()) for i,t in f]
def prepare(cues):
 src=words();ns=[norm(t) for _,t in src];cur=last=cc=0
 for cue in cues:
  needle=norm(cue["text"]);pos=next((i for i in range(cur,len(src)) if ns[i]==needle),-1)
  if pos<0:pos=next((i for i in range(len(src)) if ns[i]==needle),-1)
  if pos>=0:last,cur=src[pos][0],pos+1
  cue["sourceIndex"]=last
 for text,target in SEGMENTS:
  count=len(re.findall(r"\S+",text))
  if isinstance(target,int):
   for i,cue in enumerate(cues[cc:cc+count]):cue.update(targetPatch=target,targetWord=i)
  cc+=count
async def main():
 out=ROOT/"content"/"rehema";name="page-056-v9.mp3";cues=[]
 with (out/name).open("wb") as audio:
  stream=edge_tts.Communicate(TEXT,VOICE,rate="-8%",boundary="WordBoundary")
  async for e in stream.stream():
   if e["type"]=="audio":audio.write(e["data"])
   elif e["type"]=="WordBoundary":
    s,d=e["offset"]/10_000_000,e["duration"]/10_000_000;cues.append({"text":e["text"],"start":round(s,6),"end":round(s+d,6)})
 prepare(cues);entry={"audio":name,"voice":VOICE,"version":9,"words":cues};(out/"page-056.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8");p=out/"timecodes.json";data=json.loads(p.read_text(encoding="utf-8"));data["56"]=entry;p.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8");print(f"voice={VOICE} words={len(cues)} audio={(out/name).stat().st_size}")
if __name__=="__main__":asyncio.run(main())
