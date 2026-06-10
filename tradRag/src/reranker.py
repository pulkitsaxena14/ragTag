from sentence_transformers import CrossEncoder

from config import TOP_K_RERANK


class Reranker:

    def __init__(self):

        self.model = CrossEncoder(
            "BAAI/bge-reranker-base"
        )

    def rerank(self, query, chunks):

        pairs = [
            (query, chunk["text"])
            for chunk in chunks
        ]

        scores = self.model.predict(pairs)

        ranked = sorted(
            zip(chunks, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            item[0]
            for item in ranked[:TOP_K_RERANK]
        ]