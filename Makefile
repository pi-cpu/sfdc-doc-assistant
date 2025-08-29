# Makefile（ローカルでもCIでも同じコマンド）
export PYTHONWARNINGS=ignore

.PHONY: all crawl convert index refresh query clean
all: refresh

crawl:
	python -m rag.crawl

convert:
	python -m rag.html_to_md

index:
	python -m rag.chunk_and_index

refresh: crawl convert index

query:
	python -m rag.query "How many SOQL queries are allowed per transaction?"

clean:
	rm -rf rag/db rag/md/* rag/raw/* rag/meta/*
