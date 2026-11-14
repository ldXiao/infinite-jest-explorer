/* ---------- keyword + synonym search ---------- */
const STOP=new Set('a an the and or of in on at to with by for from who whom whose which that this those these is was were be been are has had have his her him he she they them their its it as do did does find show me all every each how wrote write written tell any some someone somebody person people character characters guy girl woman man one ones about into get got gets'.split(' '));
const norm=s=>String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[’'“”".,;:!?()]/g,' ').replace(/\s+/g,' ').trim();
const SYNIDX={}, PHRASES=[];
for(const [c,ws] of Object.entries(SRCH.syn)) for(const w of ws){ const k=norm(w); (SYNIDX[k]=SYNIDX[k]||new Set()).add(c); if(k.includes(' ')) PHRASES.push(k); }
PHRASES.sort((a,b)=>b.length-a.length);
const conceptsOf=w=>{ const s=new Set(SYNIDX[w]||[]); if(SRCH.syn[w]) s.add(w);
  if(w.length>3 && w.endsWith('s')){ const b=w.slice(0,-1); (SYNIDX[b]||[]).forEach(c=>s.add(c)); if(SRCH.syn[b]) s.add(b); } return s; };
function parseQuery(q){
  let t=' '+norm(q)+' '; const groups=[];
  for(const p of PHRASES){ if(t.includes(' '+p+' ')){ groups.push({lit:p,cons:SYNIDX[p]}); t=t.split(' '+p+' ').join(' '); } }
  for(const w of t.trim().split(' ')){ if(!w||STOP.has(w)) continue; groups.push({lit:w,cons:conceptsOf(w)}); }
  return groups;
}
const NODETXT={};
DATA.nodes.forEach(n=>{ NODETXT[n.id]={name:norm(n.name+' '+(n.aka||[]).join(' ')), desc:' '+norm(n.desc)+' ', tags:SRCH.tags[n.id]||[], facts:(SRCH.facts[n.id]||[]).map(f=>' '+norm(f.t)+' ')}; });
const synHit=(txt,g)=>wordHit(txt,g.lit)||[...g.cons].some(c=>(SRCH.syn[c]||[]).some(w=>w.length>=3&&wordHit(txt,norm(w))));
const wordHit=(txt,w)=> w.length>=4 ? txt.includes(' '+w) : txt.includes(' '+w+' ');
function matchGroup(id,g){
  const t=NODETXT[id];
  if(wordHit(' '+t.name+' ',g.lit)) return {s:3,why:null};
  if(t.facts.some(f=>wordHit(f,g.lit))||wordHit(t.desc,g.lit)) return {s:2.5,why:null};
  for(const tag of t.tags){ if(g.cons.has(tag) || tag===g.lit || (g.lit.length>=4 && tag.startsWith(g.lit))) return {s:2,why:tag.replace(/-/g,' ')}; }
  if(t.facts.some(f=>synHit(f,g))) return {s:1.5,why:null};
  if(synHit(t.desc,g)) return {s:1,why:null};
  return null;
}
/* returns [{n,cov,score,why[]}] sorted; cov = number of query terms matched, of total */
function searchChars(q){
  const groups=parseQuery(q); if(!groups.length) return {groups,hits:[]};
  const hits=[];
  for(const n of DATA.nodes){ let cov=0,score=0; const why=[];
    for(const g of groups){ const m=matchGroup(n.id,g); if(m){cov++; score+=m.s; if(m.why&&!why.includes(m.why)) why.push(m.why);} }
    if(cov){ const fs=(SRCH.facts[n.id]||[]).map((f,k)=>({f,c:groups.filter(g=>synHit(NODETXT[n.id].facts[k],g)).length})).filter(x=>x.c).sort((a,b)=>b.c-a.c).slice(0,4).map(x=>x.f);
      hits.push({n,cov,score,why,facts:fs}); }
  }
  hits.sort((a,b)=>b.cov-a.cov||b.score-a.score||(b.n.mentions||0)-(a.n.mentions||0));
  return {groups,hits};
}
/* best matches only: every term matched, else the best coverage reached */
function topHits(q){ const {groups,hits}=searchChars(q); if(!hits.length) return []; const m=hits[0].cov; return hits.filter(h=>h.cov===m); }
function eventMatches(ev,groups){
  const txt=' '+norm(ev.date+' '+ev.text+' '+ev.who.map(w=>byId[w]?byId[w].name+' '+(byId[w].aka||[]).join(' '):'').join(' '))+' ';
  return groups.every(g=>synHit(txt,g));
}

/* ---------- optional in-browser embeddings (all-MiniLM-L6-v2, int8, onnxruntime-web) ---------- */
const SMART={on:false,state:'off',sess:null,vocab:null,M:null};
function loadScript(src){ return new Promise((ok,err)=>{ const s=document.createElement('script'); s.src=src; s.onload=ok; s.onerror=()=>err(new Error('could not load '+src)); document.head.appendChild(s); }); }
async function fetchBytes(url,onProg){ const r=await fetch(url); if(!r.ok) throw new Error(url+' '+r.status);
  const total=+r.headers.get('content-length')||0, rd=r.body.getReader(), parts=[]; let got=0;
  for(;;){ const {done,value}=await rd.read(); if(done) break; parts.push(value); got+=value.length; onProg&&onProg(got,total); }
  const out=new Uint8Array(got); let o=0; for(const p of parts){out.set(p,o); o+=p.length;} return out; }
async function smartLoad(status){
  if(SMART.sess) return;
  const base=new URL('./',document.baseURI).href;
  const B=Uint8Array.from(atob(VECS.b64),c=>c.charCodeAt(0)), I=new Int8Array(B.buffer), D=VECS.dim;
  const unpack=(V)=>{ const B=Uint8Array.from(atob(V.b64),c=>c.charCodeAt(0)), I=new Int8Array(B.buffer), D=V.dim;
    return V.ids.map((id,i)=>{ const v=new Float32Array(D); let s=0; for(let k=0;k<D;k++){v[k]=I[i*D+k]; s+=v[k]*v[k];} s=Math.sqrt(s); for(let k=0;k<D;k++) v[k]/=s; return {id,k:V.k?V.k[i]:null,v}; }); };
  SMART.F=unpack(FVECS);
  SMART.M=VECS.ids.map((id,i)=>{ const v=new Float32Array(D); let s=0; for(let k=0;k<D;k++){v[k]=I[i*D+k]; s+=v[k]*v[k];} s=Math.sqrt(s); for(let k=0;k<D;k++) v[k]/=s; return {id,v}; });
  status('Loading the search engine…');
  await loadScript(base+'ort.wasm.min.js');
  ort.env.wasm.wasmPaths=base; ort.env.wasm.numThreads=1; ort.env.wasm.proxy=false;
  const voc=await (await fetch(base+'vocab.txt')).text(); SMART.vocab=new Map(voc.split('\n').map((w,i)=>[w,i]));
  let got=[0,0]; const prog=k=>(g,t)=>{got[k]=g; status(`Downloading language model… ${Math.round((got[0]+got[1])/1e6)} of 23 MB`);};
  const [a,b]=await Promise.all([fetchBytes(base+'model.part1.wasm',prog(0)),fetchBytes(base+'model.part2.wasm',prog(1))]);
  const m=new Uint8Array(a.length+b.length); m.set(a); m.set(b,a.length);
  status('Starting the model…');
  SMART.sess=await ort.InferenceSession.create(m,{executionProviders:['wasm']});
}
function wordpiece(text){
  const V=SMART.vocab, ids=[101];
  const t=text.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');
  const words=t.match(/[\p{L}\p{N}]+|[^\s\p{L}\p{N}]/gu)||[];
  for(const w of words){ if(w.length>100){ids.push(100);continue;} let s=0; const sub=[]; let bad=false;
    while(s<w.length){ let e=w.length, cur=null; while(s<e){ const p=(s?'##':'')+w.slice(s,e); if(V.has(p)){cur=V.get(p);break;} e--; } if(cur===null){bad=true;break;} sub.push(cur); s=e; }
    if(bad) ids.push(100); else ids.push(...sub); if(ids.length>250) break; }
  ids.push(102); return ids;
}
async function embed(text){
  const ids=wordpiece(text), n=ids.length, T=ort.Tensor;
  const out=await SMART.sess.run({input_ids:new T('int64',BigInt64Array.from(ids.map(BigInt)),[1,n]),
    attention_mask:new T('int64',new BigInt64Array(n).fill(1n),[1,n]), token_type_ids:new T('int64',new BigInt64Array(n),[1,n])});
  const h=out.last_hidden_state.data, D=384, v=new Float32Array(D);
  for(let i=0;i<n;i++) for(let k=0;k<D;k++) v[k]+=h[i*D+k];
  let s=0; for(let k=0;k<D;k++) s+=v[k]*v[k]; s=Math.sqrt(s); for(let k=0;k<D;k++) v[k]/=s; return v;
}
async function smartRank(q){
  const qv=await embed(q), kw=searchChars(q), ng=Math.max(1,kw.groups.length), byKw=Object.fromEntries(kw.hits.map(h=>[h.n.id,h]));
  const dot=v=>{ let c=0; for(let k=0;k<v.length;k++) c+=v[k]*qv[k]; return c; };
  const bestF={}; for(const f of SMART.F){ const c=dot(f.v); if(!bestF[f.id]||c>bestF[f.id].c) bestF[f.id]={c,k:f.k}; }
  return SMART.M.map(({id,v})=>{ const c0=dot(v), bf=bestF[id], c=Math.max(c0, bf?bf.c:-1), h=byKw[id];
    const sc=c+0.12*(h?h.cov/ng:0);
    const facts = bf && bf.c>=c0-0.02 ? [SRCH.facts[id][bf.k]] : (h?h.facts:[]);
    return {n:byId[id],sim:Math.min(1,sc),score:sc,why:h?h.why:[],facts}; }).sort((a,b)=>b.score-a.score);
}
