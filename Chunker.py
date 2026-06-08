import re
from functools import lru_cache
from transformers import AutoTokenizer

_SOFT_LIMIT = 4000  # tokens


@lru_cache(maxsize=4)
def _get_tokenizer(model: str):
    return AutoTokenizer.from_pretrained(model)


def chunk(md: str, model: str = "Qwen/Qwen3-8B", split_oversized: bool = False) -> list[dict]:
    tok = _get_tokenizer(model)

    def token_count(text: str) -> int:
        return len(tok.encode(text, add_special_tokens=False))

    # Split into raw sections at header boundaries.
    sections = []
    for block in re.split(r'(?m)^(?=#)', md.strip()):
        block = block.strip()
        if not block:
            continue
        first_line = block.split('\n', 1)[0]
        title = re.sub(r'^#+\s*', '', first_line).strip()
        # PDFs carry reliable docling section headers, so a section that exceeds
        # the soft limit is kept intact. Text formats (txt/html) may hold a huge
        # header-less block; those get sub-split on natural boundaries so chunks
        # stay bounded without cutting table rows.
        pieces = _split_oversized(block, token_count, tok) if split_oversized else [block]
        for piece in pieces:
            sections.append({"title": title, "content": piece, "tokens": token_count(piece)})

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


def _split_oversized(content: str, token_count, tok) -> list[str]:
    """Break a section over the soft limit into bounded pieces along natural
    boundaries: paragraphs first, then lines (table rows split between rows,
    never mid-row). Only a single line still over the limit falls back to a hard
    token-window cut."""
    if token_count(content) <= _SOFT_LIMIT:
        return [content]
    pieces = []
    for para in re.split(r'\n\s*\n', content):
        para = para.strip()
        if not para:
            continue
        if token_count(para) <= _SOFT_LIMIT:
            pieces.append(para)
        else:
            pieces.extend(_split_lines(para, token_count, tok))
    return pieces


def _split_lines(text: str, token_count, tok) -> list[str]:
    """Pack whole lines up to the soft limit (keeps table rows intact). A single
    line over the limit is hard-split by token window as a last resort."""
    pieces = []
    buf = []
    buf_tokens = 0
    for line in text.split('\n'):
        lt = token_count(line)
        if lt > _SOFT_LIMIT:
            if buf:
                pieces.append('\n'.join(buf))
                buf, buf_tokens = [], 0
            pieces.extend(_token_windows(line, tok))
            continue
        if buf and buf_tokens + lt > _SOFT_LIMIT:
            pieces.append('\n'.join(buf))
            buf, buf_tokens = [], 0
        buf.append(line)
        buf_tokens += lt
    if buf:
        pieces.append('\n'.join(buf))
    return pieces


def _token_windows(text: str, tok) -> list[str]:
    ids = tok.encode(text, add_special_tokens=False)
    return [tok.decode(ids[i:i + _SOFT_LIMIT]).strip() for i in range(0, len(ids), _SOFT_LIMIT)]


def _emit(sections: list[dict], seen_titles: list[str]) -> dict:
    return {
        "title": sections[0]["title"],
        "sections": [s["title"] for s in sections],
        "breadcrumb": list(seen_titles),
        "content": "\n\n".join(s["content"] for s in sections),
    }
