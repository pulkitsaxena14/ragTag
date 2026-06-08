from __future__ import annotations

import json
import re
from typing import Type, get_args, get_origin

import ollama
from pydantic import BaseModel


def _user_message(chunk: dict) -> str:
    breadcrumb = " > ".join(chunk.get("breadcrumb", [])) or "(document root)"
    sections = ", ".join(chunk.get("sections", []))
    return (
        f"## Document location\n{breadcrumb}\n\n"
        f"## Sections in this chunk\n{sections}\n\n"
        f"---\n\n"
        f"{chunk.get('content', '')}"
    )


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def _norm(s: str) -> str:
    """Whitespace-normalized (but case-preserving) text for substring checks."""
    return re.sub(r'\s+', ' ', s or '').strip()


def _salvage_validate(schema: Type[BaseModel], data: dict) -> BaseModel:
    """Build the model item-by-item, dropping individual items that fail
    validation instead of discarding the whole chunk (the all-or-nothing
    failure mode that previously lost good extractions)."""
    clean: dict = {}
    for name, field in schema.model_fields.items():
        ann = field.annotation
        val = data.get(name)
        if get_origin(ann) is list and isinstance(val, list):
            (item_t,) = get_args(ann)
            good = []
            for item in val:
                try:
                    good.append(item_t.model_validate(item) if hasattr(item_t, "model_validate") else item)
                except Exception:
                    pass  # drop the bad item, keep the rest
            clean[name] = good
        elif val is not None:
            clean[name] = val
    return schema.model_validate(clean)


# Items whose grounding (verbatim) quote must appear in the chunk text.
_VERBATIM_FIELDS = [("directives", "verbatim"), ("fundingFigures", "verbatim"), ("researchDomains", "verbatim_match")]


def _drop_unverbatim(model: BaseModel, content: str) -> BaseModel:
    """Enforce the verbatim contract: drop any item whose quote is not an exact
    (whitespace-normalized) substring of the chunk. This is the correctness
    guarantee a small local model needs."""
    hay = _norm(content)
    for field, attr in _VERBATIM_FIELDS:
        items = getattr(model, field, None)
        if not isinstance(items, list):
            continue
        kept = [it for it in items if _norm(getattr(it, attr, "")) and _norm(getattr(it, attr, "")) in hay]
        dropped = len(items) - len(kept)
        if dropped:
            print(f"    dropped {dropped} {field} (verbatim not found in chunk)")
        setattr(model, field, kept)
    return model


def preload(
    model: str,
    system_prompt: str,
    num_ctx: int,
    think: bool = False,
) -> None:
    """Load the model with the target context size and warm the constant
    system-prompt prefix so the loop's first chunk isn't cold. The model then
    stays resident via Ollama's default keep-alive (5m) — far longer than the
    gaps between chunks — and unloads on its own after the run.

    Assumes Ollama is running and the model is pulled. (Future: auto-start
    `ollama serve` / auto-pull a missing model — left out for now.)"""
    ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "ready?"},
        ],
        think=think,
        options={"temperature": 0, "num_ctx": num_ctx, "num_predict": 1},
    )


def extract_chunk(
    chunk: dict,
    model: str,
    system_prompt: str,
    schema: Type[BaseModel],
    num_ctx: int = 32768,
    num_predict: int = -1,   # -1 = no output cap (avoids JSON truncation on dense chunks)
    think: bool = False,     # Qwen3: top-level flag; Ollama injects /think or /no_think
) -> BaseModel:
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": _user_message(chunk)},
        ],
        format=schema.model_json_schema(),
        think=think,
        options={
            "temperature": 0,
            "num_ctx": num_ctx,
            "num_predict": num_predict,
        },
    )
    text = _strip_fences(response.message.content)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"    [warn] invalid JSON ({e}); emitting empty extraction")
        return schema()
    model_obj = _salvage_validate(schema, data)
    return _drop_unverbatim(model_obj, chunk.get("content", ""))
