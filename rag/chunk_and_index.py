# rag/chunk_and_index.py
import os, pathlib, json, math
import chromadb
from openai import OpenAI
from .util import MD, META, DB_DIR

EMBED_MODEL = os.getenv("EMBED_MODEL","text-embedding-3-small")
client = OpenAI()

def split_chunks(text:str, max_tokens=500):
    # 雑に段落単位で分割→長い段落は文でさらに分割
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks=[]
    for p in paras:
        # おおよそのトークン見積もり：英語なら4 chars ~ 1 token
        if len(p)/4 <= max_tokens:
            chunks.append(p); continue
        sents = [s.strip() for s in p.split(". ") if s.strip()]
        buf=""
        for s in sents:
            if (len(buf)+len(s))/4 > max_tokens:
                chunks.append(buf); buf=s
            else:
                buf = (buf+" "+s).strip()
        if buf: chunks.append(buf)
    return chunks

def main():
    chroma = chromadb.PersistentClient(path=str(DB_DIR))
    col = chroma.get_or_create_collection("sfdc_docs")
    for meta in META.glob("*.json"):
        info = json.loads(meta.read_text(encoding="utf-8"))
        url_id = meta.stem
        md_file = MD / f"{url_id}.md"
        if not md_file.exists(): continue
        text = md_file.read_text(encoding="utf-8")
        chunks = split_chunks(text, max_tokens=500)
        # 既存IDを消して差し替え（シンプルに）
        ids=[f"{url_id}_{i}" for i in range(len(chunks))]
        # いったん削除（存在しなくてもOK）
        try: col.delete(ids=ids)
        except: pass
        # 埋め込み
        for i, ck in enumerate(chunks):
            emb = client.embeddings.create(model=EMBED_MODEL, input=ck).data[0].embedding
            col.add(
                ids=[ids[i]],
                embeddings=[emb],
                documents=[ck],
                metadatas=[{
                    "url": info["url"],
                    "saved_at": info.get("saved_at"),
                    "last_modified": info.get("last_modified")
                }]
            )
        print(f"[indexed] {info['url']} -> {len(chunks)} chunks")

if __name__ == "__main__":
    main()
