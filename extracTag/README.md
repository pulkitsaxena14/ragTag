# extracTag

An extraction-first RAG pipeline: documents are parsed, chunked, and run
through a local LLM to pull structured, verbatim facts into JSON for later
analysis.

## Pipeline

```
data/inputs/ (.pdf / .htm / .html / .txt / .md)
      │
      ▼
   Parser   →  data/parsed/    (markdown + docling JSON)
      │
      ▼
   Chunker  →  data/chunks/    (header-aware, token-bounded chunks)
      │
      ▼
  Extractor →  data/extracted/ (structured JSON per chunk, via local LLM)
```

## Setup

```bash
conda create -n ragtag python=3.11
conda activate ragtag
pip install -r requirements.txt
```

Requires [Ollama](https://ollama.com) running locally with the model pulled:

```bash
ollama pull qwen3.5:9b
```

## Usage

Place input documents in `data/inputs/`, then:

```bash
python run.py
```