import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0]=[os.path.join(ROOT,'src'),os.path.join(ROOT,'tools')]
import json
s = open(os.path.join(ROOT,'src','base.html')).read()
def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:80])
    s = s.replace(old, new)

srch = json.load(open(os.path.join(ROOT,'data','search.json')))
vecs = json.load(open(os.path.join(ROOT,'data','vecs.json')))
fvecs = json.load(open(os.path.join(ROOT,'data','fvecs.json')))
js = open(os.path.join(ROOT,'src','search.js')).read()

# 1. CSS
rep('.castrow .who .map{color:var(--muted)}',
    '.castrow .who .map{color:var(--muted)}\n'
    '.why{display:flex;flex-wrap:wrap;gap:4px;margin:4px 0 0}.why span{font-size:11px;background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:1px 6px;color:var(--muted)}\n'
    '.why .sim{color:var(--accent);border-color:var(--accent)}\n'
    '.fact{font-size:13.5px;margin:6px 0 2px;padding-left:10px;border-left:3px solid var(--accent)}.fact .ref{display:block;margin-top:1px}\n'
    '.factbox{margin-top:14px}.factbox summary{cursor:pointer}.facts{list-style:none;padding:0;margin:6px 0 0}.facts li{margin:0 0 9px;font-size:14px}\n'
    '.smart{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--ink);cursor:pointer;user-select:none}\n'
    '#smartst{font-size:12.5px;color:var(--muted);margin:0 0 8px}#smartst:empty{display:none}\n'
    '.qhelp{font-size:12.5px;color:var(--muted);margin:-4px 0 8px}')

# 2. placeholders + toggle
rep('placeholder="Find a character (e.g. Gately, the Moms, prosecutor, Lyle)"',
    'placeholder="Find a character: a name, or a description (e.g. killed himself with a gun, wheelchair spy)"')
rep('<input type="search" id="cq" placeholder="Search names and descriptions"><select id="cg"><option value="">All groups</option></select></div>',
    '<input type="search" id="cq" placeholder="Describe who you want (e.g. killed himself with a gun, cross-dressing spy)"><select id="cg"><option value="">All groups</option></select>'
    '<label class="smart" title="Runs a small language model in your browser. Nothing is sent anywhere."><input type="checkbox" id="smart"> Smart search</label></div>\n'
    '  <div class="qhelp">Matches names, descriptions and fact tags, and understands synonyms (gun → pistol, Glock; killed himself → suicide). Smart search ranks by meaning instead, for looser questions; it downloads a 38 MB model the first time.</div>\n'
    '  <div id="smartst"></div>')
rep('placeholder="Filter events (e.g. Eschaton, Joelle, microwave)"', 'placeholder="Filter events (e.g. Eschaton, Joelle, suicide, overdose)"')

# 3. data + search code after esc()
anchor = "const esc = s => String(s).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));"
rep(anchor, anchor + '\nconst SRCH = ' + json.dumps(srch, ensure_ascii=False, separators=(',', ':')) + ';\nconst VECS = ' + json.dumps(vecs, separators=(',', ':')) + ';\nconst FVECS = ' + json.dumps(fvecs, separators=(',', ':')) + ';\n' + js)

# 4. graph highlight uses the ranked search
rep("""  const match = d => !q || (d.name+' '+(d.aka||[]).join(' ')).toLowerCase().includes(q);""",
    """  const hitIds = q ? new Set(topHits(q).map(h=>h.n.id)) : null;
  const match = d => !q || hitIds.has(d.id);""")
rep("""  const hits=q?DATA.nodes.filter(d=>gOn.has(d.group)&&(d.name+' '+(d.aka||[]).join(' ')).toLowerCase().includes(q)):[];""",
    """  const hits=q?topHits(q).map(h=>h.n).filter(d=>gOn.has(d.group)):[];""")

# 5. cast list: ranked results, reasons, smart mode
rep("""function drawCast(){
  const q=document.getElementById('cq').value.trim().toLowerCase(), grp=document.getElementById('cg').value;
  const list=sorted.filter(n=>(!grp||n.group===grp)&&(!q||(n.name+' '+(n.aka||[]).join(' ')+' '+n.desc).toLowerCase().includes(q)));
  document.getElementById('ccount').textContent=list.length+' of '+DATA.nodes.length+' characters';
  castEl.innerHTML=list.map(n=>{""",
"""let castSeq=0;
async function drawCast(){
  const seq=++castSeq;
  const q=document.getElementById('cq').value.trim(), grp=document.getElementById('cg').value;
  let rows, label;
  if(!q){ rows=sorted.map(n=>({n})); }
  else if(SMART.on && SMART.sess){
    let r; try{ r=await smartRank(q); }catch(e){ smartStatus('Smart search failed: '+e.message); return; }
    if(seq!==castSeq) return;
    rows=r.slice(0,25); label='closest 25 by meaning';
  } else { const {groups,hits}=searchChars(q); const full=hits.filter(h=>h.cov===groups.length);
    rows = full.length ? hits.filter(h=>h.cov===groups.length || h.cov>=Math.max(1,groups.length-1)) : hits;
    label = full.length ? (full.length===1?'1 matches every term':full.length+' match every term') : 'no character matches every term; showing partial matches'; }
  rows=rows.filter(r=>!grp||r.n.group===grp);
  const full=q&&!(SMART.on&&SMART.sess)?searchChars(q).groups.length:0;
  document.getElementById('ccount').textContent = q ? `${rows.length} result${rows.length===1?'':'s'} · ${label}` : rows.length+' of '+DATA.nodes.length+' characters';
  castEl.innerHTML=rows.map(r=>{ const n=r.n;
    const why=(r.sim!==undefined?[`<span class="sim">${Math.round(r.sim*100)}% match</span>`]:[]).concat((r.why||[]).map(w=>`<span>${esc(w)}</span>`)).concat(full&&r.cov&&r.cov<full?[`<span>${r.cov} of ${full} terms</span>`]:[]);""")
rep("""    <div class="cdesc">${esc(n.desc)}</div>${refHTML(n.first)}""",
    """    <div class="cdesc">${esc(n.desc)}</div>${why.length?`<div class="why">${why.join('')}</div>`:''}${(r.facts||[]).map(f=>`<div class="fact">${esc(f.t)} ${refHTML(f)}</div>`).join('')}${refHTML(n.first)}""")
rep("""document.getElementById('cq').addEventListener('input',drawCast); cg.addEventListener('change',drawCast);""",
"""let castT; document.getElementById('cq').addEventListener('input',()=>{ clearTimeout(castT); castT=setTimeout(drawCast, SMART.on?250:0); }); cg.addEventListener('change',drawCast);
const smartEl=document.getElementById('smartst'); const smartStatus=t=>smartEl.textContent=t;
document.getElementById('smart').addEventListener('change',async e=>{
  SMART.on=e.target.checked;
  if(SMART.on && !SMART.sess){ try{ await smartLoad(smartStatus); smartStatus('Smart search is on. Results are ranked by meaning; the % shows how close each one is in meaning.'); }
    catch(err){ SMART.on=false; e.target.checked=false; smartStatus('Smart search could not start in this browser ('+err.message+'). Keyword search still works.'); } }
  else if(SMART.on) smartStatus('Smart search is on. Results are ranked by meaning; the % shows how close each one is in meaning.');
  else smartStatus('');
  drawCast();
});""")

# 6. timeline filter with synonyms
rep("""  yearsEl.querySelectorAll('.ev').forEach(ev=>ev.classList.toggle('hide', !!q && !ev.dataset.s.includes(q)));""",
"""  const groups=q?parseQuery(q):[]; const evs=YEARS.flatMap(y=>y.events);
  yearsEl.querySelectorAll('.ev').forEach((ev,i)=>ev.classList.toggle('hide', !!q && !ev.dataset.s.includes(q) && !(groups.length && eventMatches(evs[i],groups))));""")

open(os.path.join(ROOT,'site','index.html'), 'w').write(s)
print(len(s))
s = open(os.path.join(ROOT,'site','index.html')).read()
old = '   <div class="lbl" style="margin-top:14px">Connections (${rels.length})</div>'
assert s.count(old) == 1
s = s.replace(old, '   ${(SRCH.facts[id]||[]).length?`<details class="factbox"><summary class="lbl">Facts (${SRCH.facts[id].length}) · spoilers</summary><ul class="facts">${SRCH.facts[id].map(f=>`<li>${esc(f.t)}${refHTML(f)}</li>`).join(\'\')}</ul></details>`:\'\'}\n' + old)
open(os.path.join(ROOT,'site','index.html'), 'w').write(s)
print('panel ok')
