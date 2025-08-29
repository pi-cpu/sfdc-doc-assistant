# rag/crawl.py
import re, time, yaml, requests, pathlib, urllib.parse, urllib.robotparser
from bs4 import BeautifulSoup
from .util import RAW, META, sha256_bytes, write_json, read_json, now_iso
CONFIG = yaml.safe_load((pathlib.Path("config/sources.yml")).read_text(encoding="utf-8"))
RULES  = yaml.safe_load((pathlib.Path("config/crawl_rules.yml")).read_text(encoding="utf-8"))

UA     = RULES["user_agent"]
RATE   = float(RULES["rate_limit_seconds"])
TIMEOUT= int(RULES["timeout_seconds"])
HEADERS= RULES.get("request_headers", {})
RESPECT= RULES.get("respect_robots_txt", True)

ALLOW  = [re.compile(p) for p in CONFIG["allow_patterns"]]
DENY   = [re.compile(p) for p in CONFIG["deny_patterns"]]
MAX_DEPTH = CONFIG["max_depth"]
MAX_PAGES = CONFIG["max_pages"]

def allowed(url:str)->bool:
    if any(p.search(url) for p in DENY): return False
    return any(p.search(url) for p in ALLOW)

def robots_ok(url:str)->bool:
    if not RESPECT: return True
    pr = urllib.parse.urlparse(url)
    robots_url = f"{pr.scheme}://{pr.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url); rp.read()
        return rp.can_fetch(UA, url)
    except:
        return True

def fetch(url:str):
    if not robots_ok(url): return None, None, None
    time.sleep(RATE)
    r = requests.get(url, headers={"User-Agent":UA, **HEADERS}, timeout=TIMEOUT)
    r.raise_for_status()
    etag   = r.headers.get("ETag")
    lm     = r.headers.get("Last-Modified")
    return r.content, etag, lm

def extract_links(url:str, html:bytes):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(url, a["href"])
        if href.startswith("http"):
            links.append(href.split("#")[0])
    return list(dict.fromkeys(links))

def crawl():
    visited=set()
    queue=[(u,0) for u in CONFIG["seed_urls"] if allowed(u)]
    pages=0
    while queue and pages<MAX_PAGES:
        url, depth = queue.pop(0)
        if url in visited or depth>MAX_DEPTH: continue
        visited.add(url)
        try:
            html, etag, lastmod = fetch(url)
            if not html: continue
            h = sha256_bytes(html)
            meta_path = META / (re.sub(r'[^a-zA-Z0-9]+','_',url) + ".json")
            prev = read_json(meta_path) or {}
            if prev.get("hash") == h:
                # 変更なしスキップ
                continue
            # 保存
            raw_path = RAW / (re.sub(r'[^a-zA-Z0-9]+','_',url) + ".html")
            raw_path.write_bytes(html)
            write_json(meta_path, {
                "url": url,
                "saved_at": now_iso(),
                "etag": etag,
                "last_modified": lastmod,
                "hash": h
            })
            pages+=1
            # 次リンク
            for ln in extract_links(url, html):
                if allowed(ln) and ln not in visited:
                    queue.append((ln, depth+1))
        except Exception as e:
            print("[crawl-error]", url, str(e))

if __name__ == "__main__":
    crawl()
