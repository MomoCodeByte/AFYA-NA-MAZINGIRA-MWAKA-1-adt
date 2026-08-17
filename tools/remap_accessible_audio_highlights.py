import html, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"content"/"rehema"
PAGES=[7,*range(12,23),*range(24,30),*range(31,35),37,*range(40,49),*range(51,54),57,59,63,64,66]
if len(sys.argv)>1: PAGES=[int(value) for value in sys.argv[1:]]

def norm(value):
    value=html.unescape(value).lower().replace("â€™","'").replace("â€“","-")
    value=re.sub(r"[^a-z0-9\u00c0-\u024f]+","",value)
    aliases={"moja":"1","mbili":"2","tatu":"3","nne":"4","tano":"5","sita":"6","saba":"7","nane":"8","tisa":"9","kumi":"10"}
    return aliases.get(value,value)

def page_words(page):
    raw=(ROOT/f"pg{page:03d}_sec001.html").read_text(encoding="utf-8")
    return [(int(i),html.unescape(re.sub(r"<[^>]+>","",text)).strip()) for i,text in re.findall(r'<span class="pdf-word" data-word-index="(\d+)"[^>]*>(.*?)</span>',raw,re.S)]

timecodes_path=OUT/"timecodes.json"; timecodes=json.loads(timecodes_path.read_text(encoding="utf-8"))
for page in PAGES:
    path=OUT/f"page-{page:03d}.json"; entry=json.loads(path.read_text(encoding="utf-8")); words=page_words(page); normalized=[norm(t) for _,t in words]; cursor=0; last=0
    for cue in entry.get("words",[]):
        if cue.get("targetImage") or "targetPatch" in cue: continue
        needle=norm(str(cue.get("text",""))); found=next((i for i in range(cursor,len(words)) if normalized[i]==needle),-1)
        if found<0: found=next((i for i,v in enumerate(normalized) if v==needle),-1)
        if found>=0: last=words[found][0]; cursor=found+1
        cue["sourceIndex"]=last
    path.write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding="utf-8"); timecodes[str(page)]=entry
timecodes_path.write_text(json.dumps(timecodes,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
print(f"remapped={len(PAGES)}")
