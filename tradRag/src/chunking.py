from pathlib import Path
import re

from config import CHUNK_SIZE


HEADER_PATTERN = re.compile(r"^#+\s+", re.MULTILINE)


def split_large_text_paragraphs(text: str):
    paragraphs = text.split("\n\n")
    chunks = []
    buffer = ""

    for p in paragraphs:
        if len(buffer) + len(p) > CHUNK_SIZE:
            if buffer:
                chunks.append(buffer.strip())
                # overlap: last paragraph
                overlap = buffer.split("\n\n")[-1]
                buffer = overlap + "\n\n" + p + "\n\n"
            else:
                buffer = p + "\n\n"
        else:
            buffer += p + "\n\n"

    if buffer:
        chunks.append(buffer.strip())

    return chunks

def markdown_sections(text: str):
    """
    Split markdown by headings.

    Example:

    # Chapter 1
    content

    ## Topic
    content
    """

    matches = list(HEADER_PATTERN.finditer(text))

    if not matches:
        return [text]

    sections = []

    for idx, match in enumerate(matches):

        start = match.start()

        if idx + 1 < len(matches):
            end = matches[idx + 1].start()
        else:
            end = len(text)

        sections.append(text[start:end])

    return sections


def chunk_text(text: str):

    final_chunks = []

    sections = markdown_sections(text)

    for section in sections:

        if len(section) <= CHUNK_SIZE:
            final_chunks.append(section)

        else:
            final_chunks.extend(
                split_large_text_paragraphs(section)
            )

    return final_chunks


def load_chunks(parsed_dir):

    all_chunks = []

    for file in Path(parsed_dir).glob("*.md"):

        text = file.read_text(
            encoding="utf-8"
        )

        chunks = chunk_text(text)

        for idx, chunk in enumerate(chunks):

            all_chunks.append(
                {
                    "id": f"{file.stem}_{idx}",
                    "source": file.name,
                    "text": chunk,
                }
            )

    return all_chunks