import chromadb
from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    PARSED_DIR,
    EMBED_BATCH_SIZE,
    EMBED_MODEL,
)

from chunking import load_chunks
from embeddings import embed


def build_index():

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # clean rebuild (simple demo approach)
    try:
        client.delete_collection(COLLECTION_NAME)
        print("Deleted existing collection")
    except Exception:
        pass

    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"embedding_model": EMBED_MODEL},
    )

    chunks = load_chunks(PARSED_DIR)

    print(f"Indexing {len(chunks)} chunks...")

    for i in range(0, len(chunks), EMBED_BATCH_SIZE):

        batch = chunks[i:i + EMBED_BATCH_SIZE]

        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]

        embeddings = embed(texts)

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=[{"source": c["source"]} for c in batch],
        )

        print(f"Indexed {min(i + EMBED_BATCH_SIZE, len(chunks))}/{len(chunks)}")

    print("Indexing complete")


if __name__ == "__main__":
    build_index()
