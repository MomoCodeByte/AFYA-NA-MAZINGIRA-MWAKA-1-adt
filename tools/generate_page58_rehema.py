import asyncio, html, json, re
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1];VOICE="sw-TZ-RehemaNeural"
SEGMENTS=[
 ("Matumizi ya alama za tahadhari katika mazingira yetu.",None),("Alama za tahadhari hutumika kuonya, kukataza na kuelekeza. Vilevile, hutambulisha hatari inayoweza kutokea endapo hutofuata maelekezo. Zifuatazo ni baadhi ya alama za tahadhari.",None),
 ("Alama ya moto ni pembetatu ya njano yenye ukingo mweusi na mchoro mwekundu wa mwali wa moto. Inaonya kuhusu vitu vinavyoweza kuwaka.",3),
 ("Alama ya umeme mkubwa ni pembetatu ya njano yenye ukingo mweusi na mchoro wa radi. Inaonya kuhusu hatari ya umeme.",4),
 ("Alama ya hatari ni pembetatu yenye fuvu la kichwa na mifupa. Inaonya kuhusu kitu hatari au chenye sumu.",3),
 ("Alama ya usafi wa mazingira ni duara lenye mtu akitupa taka kwenye pipa. Inaelekeza kutupa taka mahali sahihi.",5),
 ("Alama ya kivuko cha waenda kwa miguu ni pembetatu yenye mtu akitembea kwenye mistari ya kivuko. Inaonya kuhusu sehemu ya watu kuvuka barabara.",7),
 ("Alama ya mlipuko ni pembetatu ya njano yenye mchoro wa mlipuko. Inaonya kuhusu vitu vinavyoweza kulipuka.",3),
 ("Alama ya hifadhi ya wanyama ni pembetatu yenye mchoro wa mnyama. Inaonya kuwa wanyama wanaweza kuvuka eneo hilo.",5),
 ("Alama ya reli inakatisha ni pembetatu yenye mchoro wa treni. Inaonya kuhusu reli inayokatisha barabara.",4)]
TEXT=" ".join(t for t,_ in SEGMENTS)
def norm(v):return re.sub(r"[^a-z0-9\u00c0-\u024f]+","",v.lower())
def words():
 raw=(ROOT/"pg058_sec001.html").read_text(encoding="utf-8");f=re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>',raw,re.S);return [(int(i),html.unescape(re.sub(r"<[^>]+>","",t)).strip()) for i,t in f]
def prep(cues):
 src=words();ns=[norm(t) for _,t in src];cur=last=cc=0
 for cue in cues:
  n=norm(cue["text"]);pos=next((i for i in range(cur,len(src)) if ns[i]==n),-1)
  if pos<0:pos=next((i for i in range(len(src)) if ns[i]==n),-1)
  if pos>=0:last,cur=src[pos][0],pos+1
  cue["sourceIndex"]=last
 caption_indexes=[[32,33,34],[35,36,37,38],[39,40,41],[42,43,44,45,46],[47,48,49,50,51,52,53],[54,55,56],[57,58,59,60,61],[62,63,64,65]];caption=0
 for text,target in SEGMENTS:
  count=len(re.findall(r"\S+",text))
  if isinstance(target,int):
   for cue,index in zip(cues[cc:cc+target],caption_indexes[caption]):cue["sourceIndex"]=index
   for cue in cues[cc+target:cc+count]:cue["targetImage"]=True
   caption+=1
  cc+=count
async def main():
 out=ROOT/"content"/"rehema";name="page-058-v11.mp3";cues=[]
 with (out/name).open("wb") as audio:
  stream=edge_tts.Communicate(TEXT,VOICE,rate="-8%",boundary="WordBoundary")
  async for e in stream.stream():
   if e["type"]=="audio":audio.write(e["data"])
   elif e["type"]=="WordBoundary":
    s,d=e["offset"]/10_000_000,e["duration"]/10_000_000;cues.append({"text":e["text"],"start":round(s,6),"end":round(s+d,6)})
 prep(cues);entry={"audio":name,"voice":VOICE,"version":11,"words":cues};(out/"page-058.json").write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8");p=out/"timecodes.json";data=json.loads(p.read_text(encoding="utf-8"));data["58"]=entry;p.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8");print(f"voice={VOICE} words={len(cues)} audio={(out/name).stat().st_size}")
if __name__=="__main__":asyncio.run(main())
