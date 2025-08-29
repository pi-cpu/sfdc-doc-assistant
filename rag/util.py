# rag/util.py
import hashlib, json, pathlib, time
from typing import Optional

BASE = pathlib.Path(__file__).resolve().parent
RAW = BASE / "raw"
MD = BASE / "md"
META = BASE / "meta"
DB_DIR = BASE / "db"
for d in (RAW, MD, META, DB_DIR):
    d.mkdir(exist_ok=True, parents=True)

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def write_json(path: pathlib.Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def read_json(path: pathlib.Path) -> Optional[dict]:
    if not path.exists(): return None
    return json.loads(path.read_text(encoding="utf-8"))

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
