import re
from functools import lru_cache
from transformers import AutoTokenizer

_SOFT_LIMIT = 4000  # tokens; soft — a single section exceeding this is kept intact


@lru_cache(maxsize=4)
def _get_tokenizer(model: str):
    return AutoTokenizer.from_pretrained(model)


def chunk(md: str, model: str = "Qwen/Qwen3-8B") -> list[dict]:
    tok = _get_tokenizer(model)

    def token_count(text: str) -> int:
        return len(tok.encode(text, add_special_tokens=False))

    # Split into raw sections at header boundaries
    sections = []
    for block in re.split(r'(?m)^(?=#)', md.strip()):
        block = block.strip()
        if not block:
            continue
        first_line = block.split('\n', 1)[0]
        title = re.sub(r'^#+\s*', '', first_line).strip()
        sections.append({"title": title, "content": block, "tokens": token_count(block)})

    # Repack sections into token-bounded chunks
    chunks = []
    packed = []
    packed_tokens = 0
    seen_titles = []

    for section in sections:
        if packed and packed_tokens + section["tokens"] > _SOFT_LIMIT:
            chunks.append(_emit(packed, seen_titles))
            seen_titles.extend(s["title"] for s in packed)
            packed = []
            packed_tokens = 0
        packed.append(section)
        packed_tokens += section["tokens"]

    if packed:
        chunks.append(_emit(packed, seen_titles))

    return chunks


def _emit(sections: list[dict], seen_titles: list[str]) -> dict:
    return {
        "title": sections[0]["title"],
        "sections": [s["title"] for s in sections],
        "breadcrumb": list(seen_titles),
        "content": "\n\n".join(s["content"] for s in sections),
    }
