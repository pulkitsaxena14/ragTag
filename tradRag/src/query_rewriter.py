import ollama

from config import LLM_MODEL


SYSTEM_PROMPT = """
You are a query rewriting system for legislative documents.

Your job:
Convert user questions into search queries that match congressional and legislative language.

Rules:
- Do NOT answer the question
- Do NOT add new facts
- Only rewrite the query for better retrieval
- Translate abstract concepts into legislative terminology

Mapping hints:
- "research opportunities" → funding priorities, authorized studies, R&D programs, program evaluations, agency initiatives
- "future work" → reports, directives, required studies, oversight findings
- "problems" → limitations, deficiencies, compliance issues, audit findings

Return 3 rewritten queries separated by newlines.
"""


def rewrite_query(user_query: str):
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ],
        options={
            "temperature": 0.0,
        },
    )

    rewritten = response["message"]["content"]

    queries = [
        q.strip()
        for q in rewritten.split("\n")
        if q.strip()
    ]

    return queries[:3]