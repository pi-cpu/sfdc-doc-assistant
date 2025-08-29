# rag/pipeline.py
# 司令塔：crawl -> convert -> index
import subprocess, sys
stages = ["rag.crawl","rag.html_to_md","rag.chunk_and_index"]
for m in stages:
    print(f"=== {m} ===")
    subprocess.run([sys.executable,"-m",m], check=True)
print("Done.")
