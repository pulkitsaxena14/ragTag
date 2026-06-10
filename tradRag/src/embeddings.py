import ollama
from config import EMBED_MODEL


def embed(texts):
    """
    Always returns: List[List[float]]
    """
    if isinstance(texts, str):
        texts = [texts]

    response = ollama.embed(
        model=EMBED_MODEL,
        input=texts
    )
    return response["embeddings"]
