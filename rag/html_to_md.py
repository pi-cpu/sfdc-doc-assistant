# rag/html_to_md.py
import pathlib, trafilatura, re, json
from .util import RAW, MD, META

def to_md(html_text:str)->str:
    # trafilaturaで本文抽出＋見出しをMarkdown化
    md = trafilatura.extract(html_text, include_links=True, include_formatting=True)
    if not md: return ""
    # 軽微な整形：Salesforce特有の改行/空白調整など
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md

def convert():
    for meta in META.glob("*.json"):
        info = json.loads(meta.read_text(encoding="utf-8"))
        url_id = meta.stem
        raw_file = RAW / f"{url_id}.html"
        md_file  = MD  / f"{url_id}.md"
        if not raw_file.exists(): continue
        # 既に最新ならスキップ（mdの更新時刻がrawより新しければ）
        if md_file.exists() and md_file.stat().st_mtime >= raw_file.stat().st_mtime:
            continue
        html = raw_file.read_text(encoding="utf-8", errors="ignore")
        md = to_md(html)
        if not md: continue
        md_file.write_text(md, encoding="utf-8")

if __name__ == "__main__":
    convert()
