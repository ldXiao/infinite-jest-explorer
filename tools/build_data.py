import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0]=[os.path.join(ROOT,'src'),os.path.join(ROOT,'tools')]
import sys,re,json,base64,numpy as np
pass
from tags import T,GROUP,SYN
from emb import mk
s=open(os.path.join(ROOT,'src','base.html')).read()
d=json.loads(re.search(r'const DATA = (\{.*?\});\n',s).group(1))
tags={}
for n in d['nodes']:
    t=(T.get(n['id'],'')+' '+GROUP[n['group']]).split()
    tags[n['id']]=list(dict.fromkeys(t))
emb=mk(os.path.join(ROOT,'build','model.onnx'))
texts=[f"{n['name']}. {', '.join(n.get('aka') or [])}. {n['desc']} Keywords: {', '.join(x.replace('-',' ') for x in tags[n['id']])}." for n in d['nodes']]
V=emb(texts)
q=np.clip(np.round(V*127/np.abs(V).max(1,keepdims=True)),-127,127).astype(np.int8)
json.dump({'ids':[n['id'] for n in d['nodes']],'dim':384,'b64':base64.b64encode(q.tobytes()).decode()},open(os.path.join(ROOT,'data','vecs.json'),'w'))
FR=json.load(open(os.path.join(ROOT,'data','facts_resolved.json')))
facts={}
for f in FR: facts.setdefault(f['id'],[]).append({'t':f['t'],'p':f['p'],'q':f['q']})
FV=emb([f"{next(n['name'] for n in d['nodes'] if n['id']==f['id'])}: {f['t']}" for f in FR])
fq=np.clip(np.round(FV*127/np.abs(FV).max(1,keepdims=True)),-127,127).astype(np.int8)
# fact index within its character's list
cnt={}; fidx=[]
for f in FR: k=cnt.get(f['id'],0); fidx.append(k); cnt[f['id']]=k+1
json.dump({'ids':[f['id'] for f in FR],'k':fidx,'dim':384,'b64':base64.b64encode(fq.tobytes()).decode()},open(os.path.join(ROOT,'data','fvecs.json'),'w'))
json.dump({'tags':tags,'syn':SYN,'facts':facts},open(os.path.join(ROOT,'data','search.json'),'w'),ensure_ascii=False)

