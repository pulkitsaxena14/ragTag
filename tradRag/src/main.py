
from config import PARSED_DIR

from chunking import load_chunks
from retrieval import Retriever
from reranker import Reranker
from rag import generate_answer
from query_rewriter import rewrite_query


def main():

    chunks = load_chunks(PARSED_DIR)

    retriever = Retriever(chunks)
    reranker = Reranker()

    while True:

        query = input("\nQuestion: ")

        if query.lower() == "exit":
            break

        # -----------------------
        # 1. Query rewriting
        # -----------------------
        print("Rewriting query...\n" + "="*20)
        queries = rewrite_query(query)

        for q in queries:
            print("-", q)

        # -----------------------
        # 2. retrieval
        # -----------------------
        print("Starting retrieval...\n" + "="*20)
        vector_ids = []
        bm25_ids = []

        for q in queries:
            vector_ids.extend(
                retriever.vector_search(q)
            )

            bm25_ids.extend(
                retriever.bm25_search(q)
            )
        # -----------------------
        # 3. RRF fusion
        # -----------------------
        
        merged_ids = retriever.rrf(vector_ids, bm25_ids)
        
        # -----------------------
        # 4. Resolve chunks
        # -----------------------
        retrieved_chunks = [
            retriever.id_to_chunk[i]
            for i in merged_ids[:20]   # reduced for speed
        ]

        # -----------------------
        # 5. Reranking
        # -----------------------
        print("Starting rerank...\n" + "="*20)
        reranked_chunks = reranker.rerank(
            query,
            retrieved_chunks,
        )

        # -----------------------
        # 6. Generation/Output
        # -----------------------
        print("Generating answer...\n" + "="*20)
        generate_answer(
            query,
            reranked_chunks,
        )

        sources = {
            c["source"]
            for c in reranked_chunks
        }

        print("\nSources:")
        for s in sorted(sources):
            print("-", s)


if __name__ == "__main__":
    main()



