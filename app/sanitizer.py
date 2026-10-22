"""
Text sanitization, anti-adversarial normalization, and SHA-256 checksum module
conforming to VeritasDoc Engineering Specification (Phase 1, Section 3.3).
"""

import hashlib
import re
import unicodedata
from typing import Any

# Zero-width & adversarial bypass characters
ZERO_WIDTH_CHARS = [
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u00ad",  # soft hyphen
    "\u2060",  # word joiner
    "\ufeff",  # zero-width no-break space (BOM)
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
]

# Common Cyrillic & Greek homoglyphs used to evade tokenizers
HOMOGLYPH_MAP = {
    "\u0430": "a",  # Cyrillic small 'а'
    "\u0410": "A",  # Cyrillic capital 'А'
    "\u0435": "e",  # Cyrillic small 'е'
    "\u0415": "E",  # Cyrillic capital 'Е'
    "\u043e": "o",  # Cyrillic small 'о'
    "\u041e": "O",  # Cyrillic capital 'О'
    "\u0440": "p",  # Cyrillic small 'р'
    "\u0420": "P",  # Cyrillic capital 'Р'
    "\u0441": "c",  # Cyrillic small 'с'
    "\u0421": "C",  # Cyrillic capital 'С'
    "\u0443": "y",  # Cyrillic small 'у'
    "\u0445": "x",  # Cyrillic small 'х'
    "\u0425": "X",  # Cyrillic capital 'Х'
    "\u0456": "i",  # Cyrillic small 'і'
    "\u0406": "I",  # Cyrillic capital 'І'
    "\u03bf": "o",  # Greek small 'ο'
    "\u039f": "O",  # Greek capital 'Ο'
}

# Typographic ligatures
LIGATURE_MAP = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}


def compute_sha256(data: bytes) -> str:
    """Compute cryptographic SHA-256 document checksum."""
    return hashlib.sha256(data).hexdigest()


def sanitize_text(text: str) -> str:
    """
    Apply VeritasDoc Anti-Adversarial Normalization:
    1. Zero-width character removal
    2. Cyrillic/Greek homoglyph replacement
    3. Ligature disambiguation
    4. Unicode NFKC normalization
    5. Whitespace normalization
    """
    if not text:
        return ""

    # 1. Remove zero-width & stealth characters
    for zw in ZERO_WIDTH_CHARS:
        text = text.replace(zw, "")

    # 2. Replace homoglyphs
    for homoglyph, replacement in HOMOGLYPH_MAP.items():
        text = text.replace(homoglyph, replacement)

    # 3. Clean ligatures
    for lig, rep in LIGATURE_MAP.items():
        text = text.replace(lig, rep)

    # 4. Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)

    # 5. Whitespace disambiguation (non-breaking spaces, thin spaces -> regular space)
    text = re.sub(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]", " ", text)
    # Collapse multiple inline spaces while keeping newlines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\r\n|\r", "\n", text)
    # Collapse excessive vertical whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def tokenize_sentences_robust(text: str) -> list[str]:
    """
    Robust sentence boundary tokenization handling common abbreviations
    (e.g., 'Dr.', 'Prof.', 'e.g.', 'i.e.', 'et al.', 'vs.', 'Fig.', 'Eq.').
    """
    cleaned = sanitize_text(text)
    if not cleaned:
        return []

    # Protect abbreviations with placeholders
    abbreviations = [
        r"e\.g\.", r"i\.e\.", r"et al\.", r"Dr\.", r"Prof\.", r"Mr\.", r"Mrs\.",
        r"Ms\.", r"vs\.", r"Fig\.", r"Eq\.", r"Ref\.", r"Vol\.", r"No\.", r"pp\."
    ]
    placeholders: dict[str, str] = {}
    temp_text = cleaned
    for i, abbr in enumerate(abbreviations):
        matches = re.findall(abbr, temp_text, flags=re.IGNORECASE)
        for m in set(matches):
            token = f"__ABBR_{i}_{len(placeholders)}__"
            placeholders[token] = m
            temp_text = temp_text.replace(m, token)

    # Split by standard sentence delimiters (. ! ?) followed by whitespace or quote
    splits = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'‘“])", temp_text)

    sentences: list[str] = []
    for s in splits:
        s = s.strip()
        if not s:
            continue
        # Restore placeholders
        for token, orig in placeholders.items():
            s = s.replace(token, orig)
        sentences.append(s)

    # Fallback if text didn't split well
    if not sentences and cleaned:
        sentences = [cleaned]

    return sentences
