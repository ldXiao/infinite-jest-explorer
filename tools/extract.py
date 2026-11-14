import sys,re,html,json,os
root=sys.argv[1]; opf=[os.path.join(dp,f) for dp,_,fs in os.walk(root) for f in fs if f.endswith('.opf')][0]
o=open(opf,encoding='utf-8').read()
man=dict(re.findall(r'<item[^>]*id="([^"]+)"[^>]*href="([^"]+)"',o)) ; man.update({a:b for b,a in re.findall(r'<item[^>]*href="([^"]+)"[^>]*id="([^"]+)"',o)})
spine=re.findall(r'itemref idref="([^"]+)"',o)
paras=[]
for sid in spine:
    p=os.path.join(os.path.dirname(opf),man[sid]); x=open(p,encoding='utf-8').read()
    body=x.split('<body',1)[-1]
    for m in re.finditer(r'<(p|h\d|div)[^>]*>(.*?)</\1>',body,re.S):
        t=html.unescape(re.sub(r'<[^>]+>','',m.group(2))); t=re.sub(r'\s+',' ',t).strip()
        if t: paras.append({'s':sid,'t':t})
json.dump(paras,open(sys.argv[2],'w'),ensure_ascii=False)
print(len(paras), sum(len(p['t']) for p in paras))
from collections import Counter; c=Counter(p['s'] for p in paras); print(c)
