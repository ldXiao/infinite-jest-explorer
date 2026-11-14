import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0]=[os.path.join(ROOT,'src'),os.path.join(ROOT,'tools')]
import json,re,bisect
P=json.load(open(os.path.join(ROOT,'build','paras.json')))
off=[];o=0
for p in P: off.append(o); o+=len(p['t'])+1
FULL='\n'.join(p['t'] for p in P)
def norm(s): return re.sub(r'[‘’]',"'",re.sub(r'[“”]','"',s))
FN=norm(FULL)
s=open(os.path.join(ROOT,'src','base.html')).read()
D=json.loads(re.search(r'const DATA = (\{.*?\});\n',s).group(1)); Y=json.loads(re.search(r'const YEARS = (\[.*?\]);\n',s).group(1))
refs=[n['first'] for n in D['nodes']]+[l['ref'] for l in D['links'] if l.get('ref')]+[e for y in Y for e in y['events']]
pts=[]
for r in refs:
    i=FN.find(norm(r['q']))
    if i>=0: pts.append((i,r['p']))
pts=sorted(set(pts))
def page(i):
    xs=[a for a,_ in pts]; k=bisect.bisect_left(xs,i)
    if k==0: a,b=pts[0],pts[1]
    elif k>=len(pts): a,b=pts[-2],pts[-1]
    else: a,b=pts[k-1],pts[k]
    if b[0]==a[0]: return a[1]
    return round(a[1]+(b[1]-a[1])*(i-a[0])/(b[0]-a[0]))
idx={s:i for i,s in reversed(list(enumerate(p['s'] for p in P)))}
nstart=off[idx['note-1a']]; nend=off[idx['foot-1']]
pts=[x for x in pts if x[0]<nstart]+[(nstart-1,981),(nstart,983),(nend,1079)]
pts.sort()
def para_of(i): return bisect.bisect_right(off,i)-1
def g(pat,n=6,w=220,flags=re.I):
    out=[]
    for m in re.finditer(pat,FN,flags):
        i=m.start(); a=max(0,i-w); out.append(f"[{page(i)}|{P[para_of(i)]['s']}] ...{FN[a:i+w]}...".replace('\n',' / '))
        if len(out)>=n: break
    return out
def G(*pats,**k):
    for pt in pats:
        print('##',pt); [print('  ',x) for x in g(pt,**k)]
