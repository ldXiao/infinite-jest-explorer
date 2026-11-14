import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0]=[os.path.join(ROOT,'src'),os.path.join(ROOT,'tools')]
import sys,re,json; pass
from pages import FN,page,P,para_of
import importlib, facts; importlib.reload(facts)
out=[];miss=[]
for f in facts.F:
    cid,txt,rx=f[:3]; nth=f[3] if len(f)>3 else 0
    ms=list(re.finditer(rx,FN,re.S))
    if len(ms)<=nth: miss.append(f); continue
    m=ms[nth]; i=m.start()
    # quote: 6-8 words from the paragraph starting at match, no line breaks
    seg=FN[i:i+200].split('\n')[0]; w=seg.split(' ')[:7]; q=' '.join(w).strip(' ,;:—')
    q=q.strip("'\"‘’“” ")
    out.append({'id':cid,'t':txt,'p':page(i),'q':q,'_ctx':FN[max(0,i-120):i+160].replace('\n',' / ')})
json.dump([{k:v for k,v in o.items() if k!='_ctx'} for o in out],open(os.path.join(ROOT,'data','facts_resolved.json'),'w'),ensure_ascii=False,indent=0)
if '-v' in sys.argv:
    for o in out: print(f"{o['id']:<11} p{o['p']} «{o['q']}» :: {o['t'][:60]}\n    {o['_ctx']}")
print('resolved',len(out),'missing',[(m[0],m[1][:40]) for m in miss])
