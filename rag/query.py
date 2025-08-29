# rag/query.py
import os, sys, chromadb
from openai import OpenAI

CHAT_MODEL = os.getenv("CHAT_MODEL","gpt-4o-mini")

def ask(q:str):
    chroma = chromadb.PersistentClient(path=os.getenv("CHROMA_DB_PATH","rag/db"))
    col = chroma.get_collection("sfdc_docs")
    res = col.query(query_texts=[q], n_results=6)
    docs = res["documents"][0]
    metas= res["metadatas"][0]
    ctx = "\n\n---\n\n".join(
        f"[Source] {m['url']} (last_modified={m.get('last_modified')})\n{d}"
        for d,m in zip(docs, metas)
    )
    sys_prompt = (
        "You are a Salesforce documentation assistant. "
        "Answer ONLY from the provided context. If unsure, say 'Unknown' and show citations. "
        "Return: brief conclusion, bullets for key points, then 'Citations:' with URLs."
    )
    client = OpenAI()
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role":"system","content":sys_prompt},
            {"role":"user","content":f"Question: {q}\n\nContext:\n{ctx}"}
        ],
        temperature=0.2
    )
    print(resp.choices[0].message.content)

if __name__=="__main__":
    ask(sys.argv[1])
