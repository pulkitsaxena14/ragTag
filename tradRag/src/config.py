PDF_DIR = "data/pdfs"
PARSED_DIR = "data/parsed"

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "documents"

EMBED_MODEL = "qwen3-embedding"
LLM_MODEL = "qwen3.5:9b-mlx"

# Larger chunks work better for large PDFs.
CHUNK_SIZE = 3000

TOP_K_VECTOR = 20
TOP_K_BM25 = 20
TOP_K_RERANK = 5

EMBED_BATCH_SIZE = 128
