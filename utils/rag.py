
import os, re, json, hashlib, numpy as np
from dotenv import load_dotenv
from openai import OpenAI
try:
    from PyPDF2 import PdfReader
except Exception: PdfReader=None
try:
    import docx
except Exception: docx=None

load_dotenv()
api=os.getenv("OPENAI_API_KEY","").strip()
if not api: raise RuntimeError("Falta OPENAI_API_KEY")
client=OpenAI(api_key=api)

CHUNK_SIZE=950; OVERLAP=220

def split_sentences(t):
    parts = re.split(r"(?<=[\.!\?:;])\s+|\n+", t)
    return [p.strip() for p in parts if p and p.strip()]

def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    sents=split_sentences(text); chunks=[]; cur=""
    for s in sents:
        if len(cur)+len(s)+1<=size: cur+=(" " if cur else "")+s
        else:
            if cur: chunks.append(cur)
            cur=(cur[-overlap:]+" " if overlap and len(cur)>overlap else "")+s
    if cur: chunks.append(cur)
    if not chunks:
        for i in range(0,len(text),size-overlap): chunks.append(text[i:i+size])
    return chunks

def load_txt(p): return open(p,"r",encoding="utf-8",errors="ignore").read()
def load_pdf(p):
    if not PdfReader: return ""
    out=[]; rd=PdfReader(p)
    for pg in rd.pages:
        try: out.append(pg.extract_text() or "")
        except: pass
    return "\n".join(out)
def load_docx(p):
    if not docx: return ""
    d=docx.Document(p); return "\n".join(x.text for x in d.paragraphs)
def file_text(p):
    e=os.path.splitext(p)[1].lower()
    if e==".txt": return load_txt(p)
    if e==".pdf": return load_pdf(p)
    if e==".docx": return load_docx(p)
    return ""

def embed_texts(texts):
    r = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in r.data]

def cos_sim(a,b):
    a=a/(np.linalg.norm(a,axis=1,keepdims=True)+1e-12)
    b=b/(np.linalg.norm(b,axis=1,keepdims=True)+1e-12)
    return a@b.T

class RAGBase:
    def __init__(self,data_dir,cache_dir):
        self.data_dir=data_dir; self.cache_dir=cache_dir
        os.makedirs(self.cache_dir,exist_ok=True)
        self.chunks=[]; self.files=[]; self.emb=None
    def _key(self):
        h=hashlib.sha256()
        for fn in sorted(os.listdir(self.data_dir)):
            p=os.path.join(self.data_dir,fn)
            if os.path.isfile(p):
                st=os.stat(p); h.update(f"{fn}:{st.st_size}:{int(st.st_mtime)}".encode())
        return h.hexdigest()
    def build(self):
        key=self._key()
        embp=os.path.join(self.cache_dir,f"emb_{key}.npy")
        metap=os.path.join(self.cache_dir,f"meta_{key}.json")
        if os.path.exists(embp) and os.path.exists(metap):
            self.emb=np.load(embp); m=json.load(open(metap,"r",encoding="utf-8"))
            self.chunks=m["chunks"]; self.files=m["files"]; return
        chunks=[]; files=[]
        for fn in sorted(os.listdir(self.data_dir)):
            p=os.path.join(self.data_dir,fn)
            if not os.path.isfile(p): continue
            raw=file_text(p).strip()
            if not raw: continue
            for ch in chunk_text(raw): chunks.append(ch); files.append(fn)
        if not chunks: chunks=["No hay documentos en /data."]; files=["SYSTEM"]
        embs=embed_texts(chunks)
        self.emb=np.array(embs,dtype=np.float32); self.chunks=chunks; self.files=files
        np.save(embp,self.emb); json.dump({"chunks":chunks,"files":files},open(metap,"w",encoding="utf-8"),ensure_ascii=False)
    def retrieve(self,q,k=7):
        import numpy as np
        qv=np.array(embed_texts([q])[0],dtype=np.float32).reshape(1,-1)
        sims=cos_sim(qv,self.emb)[0]; idx=np.argsort(-sims)[:k]
        return [{"text":self.chunks[i],"file":self.files[i]} for i in idx]
    def answer(self,question,short=False):
        top=self.retrieve(question,k=7)
        ctx="\n\n---\n".join([f"[{t['file']}] {t['text']}" for t in top])
        style="Responde en 1–2 oraciones." if short else "Responde en un párrafo breve y claro (máx. 6 oraciones)."
        system=("Eres un asistente académico del proyecto 'Escribir para soñar'. "
                "Responde SOLO con información del CONTEXTO. "
                "Si no está, responde exactamente: 'No encuentro ese dato en los documentos.' "+style)
        user=f"Pregunta: {question}\n\nCONTEXTO:\n{ctx}"
        r = client.chat.completions.create(model="gpt-4o-mini",messages=[
            {"role":"system","content":system},
            {"role":"user","content":user}],temperature=0.15)
        return r.choices[0].message.content.strip()
