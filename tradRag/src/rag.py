import ollama

from config import LLM_MODEL


SYSTEM_PROMPT = """
For questions about funding priorities, appropriations, or research areas:

- Summarize the major funded programs mentioned.
- Include funding amounts when available.
- Do not assume rankings unless explicitly stated.
- If the context does not contain enough information to determine the top funded programs, say so.
- When possible, also infer higher-level scientific or research themes that connect multiple programs.

Be concise.
"""


def generate_answer(query, chunks):

    context = "\n\n".join(
        chunk["text"]
        for chunk in chunks[:8]  # keep prompt bounded
    )

    # print("Context length:", len(context))
    # print("Chunk count:", len(chunks[:8]))
    # print()
    prompt = f"""
    Context:

    {context}

    Question:
    {query}
    """
    
    # print("\n--- CONTEXT PREVIEW ---")
    # print(context[:2000])
    # print("\n--- END PREVIEW ---\n")

    stream = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        stream=True,
        options={
            "temperature": 0,
            "seed": 42,
        },
    )

    # print("Chat request sent")

    for chunk in stream:
        if chunk.get("think"):
            print("[think]:", chunk["think"])
        print(chunk["message"]["content"], end="", flush=True)