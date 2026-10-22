"""
Text utility functions: sentence segmentation and confidence level classification.
"""

import re

# Common English abbreviations that end with a period and should not split sentences
ABBREVIATIONS = (
    r"\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|i\.e|e\.g|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|No|Vol|pp|al|Fig|Eq)\."
)


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into individual sentences while preserving abbreviations,
    decimals, and proper boundary punctuation.
    """
    if not text or not text.strip():
        return []

    # Replace arbitrary whitespace and linebreaks with single spaces
    normalized = re.sub(r"[\r\n]+", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Split on sentence-ending punctuation followed by space and capital letter or quote
    pattern = r'(?<=[.?!])\s+(?=[A-Z0-9"\'\(\[\{])'
    raw_segments = re.split(pattern, normalized)

    sentences: list[str] = []
    buffer = ""

    for segment in raw_segments:
        seg = segment.strip()
        if not seg:
            continue
        if buffer:
            candidate = f"{buffer} {seg}"
        else:
            candidate = seg

        # Check if the split happened on an abbreviation like "Dr." or "e.g."
        if re.search(ABBREVIATIONS + r"$", candidate, flags=re.IGNORECASE):
            buffer = candidate
        else:
            sentences.append(candidate)
            buffer = ""

    if buffer:
        sentences.append(buffer)

    return sentences


def get_confidence_band(prob: float) -> str:
    """
    Compute confidence band for a given AI probability (0.0 to 1.0).
    - high:   prob >= 0.8 OR prob <= 0.2
    - medium: prob >= 0.65 OR prob <= 0.35
    - low:    otherwise (between 0.35 and 0.65)
    """
    if prob >= 0.8 or prob <= 0.2:
        return "high"
    elif prob >= 0.65 or prob <= 0.35:
        return "medium"
    return "low"
