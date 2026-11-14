import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0]=[os.path.join(ROOT,'src'),os.path.join(ROOT,'tools')]
import sys, numpy as np, onnxruntime as o
from tokenizers import BertWordPieceTokenizer
TOK=BertWordPieceTokenizer(os.path.join(ROOT,'site','vocab.txt'),lowercase=True); TOK.enable_truncation(256); TOK.no_padding()
def mk(path):
    s=o.InferenceSession(path)
    def emb(texts):
        out=[]
        for t in texts:
            e=TOK.encode(t); ids=np.array([e.ids],dtype=np.int64); m=np.ones_like(ids)
            h=s.run(None,{'input_ids':ids,'attention_mask':m,'token_type_ids':np.zeros_like(ids)})[0][0]
            v=h.mean(0); out.append(v/np.linalg.norm(v))
        return np.array(out)
    return emb
