# ragTag

A personal project for learning and experimenting with Retrieval-Augmented
Generation (RAG) architectures.

## Subprojects

Each subdirectory is an independent take on the problem, built separately so
different RAG strategies can be compared.

| Project | Approach |
|---|---|
| [`tradRag/`](tradRag/README.md) | Classic RAG: parse → chunk → embed → hybrid retrieval (vector + BM25) → rerank → LLM answer |
| [`extracTag/`](extracTag/README.md) | Extraction-first: parse → chunk → LLM-based structured extraction into a well-defined schema, for analysis later | 