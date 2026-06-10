import chromadb
from rank_bm25 import BM25Okapi

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    TOP_K_VECTOR,
    TOP_K_BM25,
)

from embeddings import embed


class Retriever:

    def __init__(self, chunks):

        self.chunks = chunks

        self.id_to_chunk = {
            c["id"]: c for c in chunks
        }

        self.bm25 = BM25Okapi(
            [c["text"].split() for c in chunks]
        )

        client = chromadb.PersistentClient(path=CHROMA_DIR)

        self.collection = client.get_collection(COLLECTION_NAME)

    def vector_search(self, query):

        query_vec = embed(query)[0]

        result = self.collection.query(
            query_embeddings=[query_vec],
            n_results=TOP_K_VECTOR,
        )

        return result["ids"][0]

    def bm25_search(self, query):

        scores = self.bm25.get_scores(query.split())

        ranked = sorted(
            zip(self.chunks, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return [c["id"] for c, _ in ranked[:TOP_K_BM25]]

    def rrf(self, vector_ids, bm25_ids, k=60):

        scores = {}

        for rank, doc_id in enumerate(vector_ids):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)

        for rank, doc_id in enumerate(bm25_ids):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [doc_id for doc_id, _ in ranked]