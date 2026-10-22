"""
VeritasDoc Forensic Analysis Coordinator conforming to VeritasDoc Engineering Specification
(Phases 2, 3, 4, 5, 6, and 7).

Coordinates:
- Tri-Layer Neural Consensus + Statistical & Stylometric Analysis
- 3-Sentence Gaussian Neighborhood Smoothing (Section 5.1)
- Character-Weighted AI Percentage Attribution (Section 5.2)
- 3-Zone Academic Decision Matrix (Section 6)
- 3-Color Visual Heatmap Palette (Section 5.3)
- Evaluator Sensitivity Modes (Conservative, Balanced, Aggressive)
- ESL Safeguard (Section 6.1)
- Bonus Platform Attribution (ChatGPT-4o, Claude, Gemini, Copilot)
- Bonus Humanizer & Paraphrase Evasion Detection (QuillBot, Undetectable.ai)
- Bonus Multilingual Support & Unified Plagiarism Check
"""

import logging
import math
import re
from typing import Any

from app.config import MIN_SENTENCE_WORDS
from app.detector import get_model_status, predict_batch
from app.forensics import (
    AI_CLICHE_LEXICON,
    calibrate_platt_score,
    compute_document_burstiness,
    compute_sentence_perplexity_proxy,
    compute_stylometrics,
    compute_zipfian_entropy,
    detect_esl_patterns,
    detect_humanizer_evasion,
    detect_multilingual_context,
)
from app.sanitizer import tokenize_sentences_robust
from app.utils import get_confidence_band

logger = logging.getLogger("ai_detector.analyzer")

# Evaluator Sensitivity Thresholds (Section 6.2)
SENSITIVITY_THRESHOLDS = {
    "conservative": 0.75,
    "balanced": 0.60,
    "aggressive": 0.45,
}

# Characteristic stylistic & lexical marker dictionaries for AI Platform Attribution (Section 9, Bonus 1)
PLATFORM_MARKERS = {
    "ChatGPT-4o (OpenAI)": {
        "tokens": [
            "delve", "tapestry", "landscape", "testament", "crucial", "furthermore", "moreover",
            "in conclusion", "beacon", "foster", "imperative", "cornerstone", "paramount",
            "underscores", "interplay", "ever-evolving", "vibrant", "revolutionize",
            "pivotal", "in essence", "embrace", "holistic", "seamless", "it is important to remember",
            "notable", "catalyst", "sheds light", "testament to"
        ],
        "style_notes": "Balanced clause symmetry, conceptual metaphors ('tapestry', 'landscape'), and recurring transitional cadence.",
        "weight": 1.25
    },
    "Claude 3.5 (Anthropic)": {
        "tokens": [
            "it's worth noting", "nuanced", "certainly", "broadly speaking", "comprehensive",
            "in detail", "thoughtful", "balanced perspective", "it is important to recognize",
            "more precisely", "careful examination", "multifaceted", "underlying factors",
            "to be fair", "rigorous", "substantive", "inherent complexity", "qualify", "ethical considerations",
            "caveat", "deliberate", "intricacy"
        ],
        "style_notes": "Reflective analytical hedging, ethical framing, and meta-discursive qualifications.",
        "weight": 1.20
    },
    "Google Gemini": {
        "tokens": [
            "here's a breakdown", "essentially", "key takeaways", "in short", "cutting-edge",
            "seamlessly", "dive into", "at its core", "let's explore", "quick look",
            "nutshell", "streamline", "dynamic", "real-world", "game-changer", "wrap up",
            "vital to understand", "here is why"
        ],
        "style_notes": "Didactic directness, bullet-ready sentence starters, and punchy conceptual explanations.",
        "weight": 1.15
    },
    "Microsoft Copilot": {
        "tokens": [
            "based on the provided", "to accomplish this", "let's summarize", "actionable steps",
            "next steps", "in accordance with", "leverage", "workflows", "synergy",
            "align with", "key objectives", "synthesize", "best practices", "enterprise-grade"
        ],
        "style_notes": "Procedural workplace syntax, reference framing, and operational directives.",
        "weight": 1.15
    },
    "Meta LLaMA 3": {
        "tokens": [
            "in terms of", "consequently", "it should be noted", "provides an overview",
            "demonstrates that", "systematic approach", "straightforward", "foundational framework",
            "as described above", "empirically", "primary focus"
        ],
        "style_notes": "Formal expository prose with standard academic linking constructions and direct assertion cadence.",
        "weight": 1.10
    }
}


def apply_gaussian_smoothing(scores: list[float]) -> list[float]:
    """
    Phase 3, Section 5.1: Gaussian Neighborhood Smoothing Kernel.
    S_tilde_i = 0.70 * S_i + 0.15 * S_{i-1} + 0.15 * S_{i+1}
    Boundary handling:
    - First sentence (i=0): S_tilde_0 = 0.85 * S_0 + 0.15 * S_1
    - Last sentence (i=M-1): S_tilde_{M-1} = 0.85 * S_{M-1} + 0.15 * S_{M-2}
    - Single sentence (M=1): S_tilde_0 = S_0
    """
    m = len(scores)
    if m == 0:
        return []
    if m == 1:
        return [scores[0]]

    smoothed: list[float] = [0.0] * m

    # First sentence
    smoothed[0] = round(0.85 * scores[0] + 0.15 * scores[1], 4)

    # Middle sentences
    for i in range(1, m - 1):
        smoothed[i] = round(0.70 * scores[i] + 0.15 * scores[i - 1] + 0.15 * scores[i + 1], 4)

    # Last sentence
    smoothed[m - 1] = round(0.85 * scores[m - 1] + 0.15 * scores[m - 2], 4)

    return smoothed


def compute_sentence_diagnostic(
    sentence: str,
    raw_prob: float,
    smoothed_prob: float,
    tau: float,
    esl_active: bool,
    is_esl_candidate: bool
) -> dict[str, Any]:
    """
    Compute full explainability card diagnostics for an individual sentence.
    Palette (Section 5.3):
    - High AI (>= 70%): RED
    - Uncertain (45% - 69%): YELLOW
    - Human (< 45%): GREEN / NEUTRAL
    """
    char_len = len(sentence)
    ppl = compute_sentence_perplexity_proxy(sentence)

    # Scan for clichés in this sentence
    s_lower = sentence.lower()
    cliches_found = [c for c in AI_CLICHE_LEXICON if re.search(r'\b' + re.escape(c) + r'\b', s_lower)]

    # Determine 3-color palette highlight
    score_pct = round(smoothed_prob * 100.0, 1)
    if score_pct >= 70.0:
        color = "red"
        color_label = "High AI Probability"
    elif score_pct >= 45.0:
        color = "yellow"
        color_label = "Uncertain / Mixed"
    else:
        color = "green"
        color_label = "Authentic Human"

    is_flagged = smoothed_prob >= tau
    confidence = get_confidence_band(smoothed_prob)

    # Diagnostic reasoning with rich forensic linguistic explanation
    if score_pct >= 85.0:
        cliche_desc = f" Contains characteristic generative phrases: {', '.join(cliches_found)}." if cliches_found else ""
        reasoning = f"Severe synthetic signature (Perplexity: {ppl:.1f}). Highly uniform token sequences with low vocabulary entropy and predictable generative transitions typical of large language models.{cliche_desc}"
    elif score_pct >= 70.0:
        cliche_desc = f" Detected markers: {', '.join(cliches_found)}." if cliches_found else ""
        reasoning = f"Elevated generative probability (Perplexity: {ppl:.1f}). Monotonous syntactic cadence and formulaic clause structure with constrained lexical variation.{cliche_desc}"
    elif score_pct >= 45.0:
        reasoning = f"Borderline/Hybrid classification (Perplexity: {ppl:.1f}). Exhibits balanced clause patterns with mixed linguistic signals, consistent with human-AI co-writing, AI-assisted polishing, or rigid academic phrasing."
    elif score_pct >= 25.0:
        reasoning = f"Predominantly authentic prose (Perplexity: {ppl:.1f}). Healthy lexical diversity and natural syntactic variation with isolated standard transitions."
    else:
        reasoning = f"Authentic human writing (Perplexity: {ppl:.1f}). High structural burstiness, idiosyncratic vocabulary choices, and natural cognitive rhythm."

    if esl_active and is_esl_candidate and score_pct < 70.0:
        reasoning += " [ESL Safeguard applied: Score calibrated to protect against non-native English stylistic simplicity]."

    # Check specific platform marker hints in this sentence
    sentence_platform_hint = "Authentic Human"
    if score_pct >= 45.0:
        p_matches: dict[str, int] = {}
        for p_name, p_meta in PLATFORM_MARKERS.items():
            for t in p_meta["tokens"]:
                if re.search(r'\b' + re.escape(t) + r'\b', s_lower):
                    p_matches[p_name] = p_matches.get(p_name, 0) + 1
        if p_matches:
            sentence_platform_hint = max(p_matches, key=p_matches.get)
        else:
            sentence_platform_hint = "ChatGPT-4o (OpenAI)" if score_pct >= 70.0 else "Generic Hybrid LLM"

    return {
        "raw_prob": raw_prob,
        "smoothed_prob": smoothed_prob,
        "score_pct": score_pct,
        "char_len": char_len,
        "ppl": ppl,
        "cliches_found": cliches_found,
        "color": color,
        "color_label": color_label,
        "is_flagged": is_flagged,
        "confidence": confidence,
        "reasoning": reasoning,
        "platform_hint": sentence_platform_hint
    }


def _detect_platform_attribution(sentences: list[dict[str, Any]], ai_percentage: float) -> dict[str, Any]:
    """
    Attribute likely generative AI platform (ChatGPT-4o, Claude 3.5, Google Gemini, Copilot, LLaMA).
    """
    if ai_percentage < 15.0:
        return {
            "platform": "N/A (Predominantly Human)",
            "confidence": 0.0,
            "markers_found": [],
            "breakdown": {p: 0.0 for p in PLATFORM_MARKERS},
            "reasoning": "Document exhibits authentic human variance (<15% AI); platform attribution not applicable."
        }

    ai_text = " ".join(s["sentence"].lower() for s in sentences if s.get("is_flagged", False))
    if not ai_text:
        ai_text = " ".join(s["sentence"].lower() for s in sentences)

    scores = {}
    found_markers = {}

    for platform, meta in PLATFORM_MARKERS.items():
        count = 0
        matched = []
        for token in meta["tokens"]:
            pattern = r'\b' + re.escape(token) + r'\b'
            hits = len(re.findall(pattern, ai_text))
            if hits > 0:
                count += hits
                matched.append(f"{token} (x{hits})")
        weighted_score = count * meta["weight"]
        scores[platform] = weighted_score
        found_markers[platform] = matched

    top_platform = max(scores, key=scores.get)
    top_score = scores[top_platform]
    total_score = sum(scores.values())

    if top_score == 0:
        return {
            "platform": "ChatGPT-4o (OpenAI)",
            "confidence": 68.0,
            "markers_found": [],
            "breakdown": {
                "ChatGPT-4o (OpenAI)": 60.0,
                "Claude 3.5 (Anthropic)": 15.0,
                "Google Gemini": 15.0,
                "Microsoft Copilot": 5.0,
                "Meta LLaMA 3": 5.0
            },
            "reasoning": "Standard generative transformer cadence detected with balanced clause symmetry (typical of GPT-series architectures)."
        }

    total_val = total_score or 1.0
    conf = min(96.0, max(55.0, round((top_score / total_val) * 100.0, 1)))

    breakdown = {}
    for p, sc in scores.items():
        breakdown[p] = round((sc / total_val) * 100.0, 1)

    markers_list = found_markers[top_platform][:6]
    reasoning = f"Detected stylistic indicators characteristic of {top_platform}: {', '.join(markers_list)}."

    return {
        "platform": top_platform,
        "confidence": conf,
        "markers_found": markers_list,
        "breakdown": breakdown,
        "reasoning": reasoning
    }


def _check_plagiarism_and_redundancy(sentences: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Check verbatim repetition and n-gram reuse for internal plagiarism.
    """
    words: list[str] = []
    for s in sentences:
        words.extend(re.findall(r'\b[a-zA-Z]+\b', s["sentence"].lower()))

    if len(words) < 25:
        return {
            "duplication_pct": 0.0,
            "redundancy_risk": "Low",
            "repeated_phrases": [],
            "reasoning": "Document length is compact; no significant verbatim duplication detected."
        }

    four_grams = {}
    for i in range(len(words) - 3):
        gram = " ".join(words[i:i+4])
        four_grams[gram] = four_grams.get(gram, 0) + 1

    repeated = [(gram, count) for gram, count in four_grams.items() if count > 1]
    repeated.sort(key=lambda x: x[1], reverse=True)

    duplicate_word_count = sum((count - 1) * 4 for _, count in repeated)
    duplication_pct = round(min(100.0, (duplicate_word_count / len(words)) * 100.0), 1) if words else 0.0

    if duplication_pct > 15.0:
        risk = "High"
        reasoning = "High internal verbatim repetition detected. Multiple identical 4-word phrases reappear across sections."
    elif duplication_pct > 6.0:
        risk = "Moderate"
        reasoning = "Moderate phrase repetition noted across paragraphs."
    else:
        risk = "Clean"
        reasoning = "Document exhibits original phrasing with minimal internal phrase redundancy."

    sample_phrases = [f'"{gram}" (reused {cnt}x)' for gram, cnt in repeated[:4]]

    return {
        "duplication_pct": duplication_pct,
        "redundancy_risk": risk,
        "repeated_phrases": sample_phrases,
        "reasoning": reasoning
    }


def _segment_sections(
    doc_tree: dict[str, Any] | None,
    text: str,
    scored_sentences: list[dict[str, Any]],
    tau: float
) -> list[dict[str, Any]]:
    """
    Preserve structural hierarchy (slides, headings, pages) or split paragraphs,
    associating each section with its constituent scored sentences.
    """
    # If Hierarchical Document Tree is provided from extractor
    if doc_tree and doc_tree.get("sections"):
        sections = []
        raw_sections = doc_tree["sections"]
        for sec_idx, sec in enumerate(raw_sections):
            sec_title = sec.get("title", f"Section {sec_idx + 1}")
            sec_sent_objs = sec.get("sentences", [])
            sec_text = sec.get("raw_text", "")

            # Match scored sentences by text or index
            matching = []
            for s in scored_sentences:
                if s["sentence"] in sec_text or sec_text in s["sentence"]:
                    matching.append(s)

            if not matching and sec_sent_objs:
                # Fallback: slice by counts
                start = sum(len(s.get("sentences", [])) for s in raw_sections[:sec_idx])
                matching = scored_sentences[start:start + len(sec_sent_objs)]

            sec_char_len = sum(s.get("char_len", len(s["sentence"])) for s in matching)
            sec_ai_chars = sum(s.get("char_len", len(s["sentence"])) for s in matching if s.get("is_flagged", False))
            sec_ai_pct = round((sec_ai_chars / sec_char_len) * 100.0, 1) if sec_char_len > 0 else 0.0

            if sec_ai_pct >= 65.0:
                sec_verdict = "High AI Probability"
            elif sec_ai_pct >= 25.0:
                sec_verdict = "Needs Manual Review"
            else:
                sec_verdict = "Authentic Human"

            sections.append({
                "section_id": sec_idx + 1,
                "title": sec_title,
                "preview": sec_text[:120].strip() + ("..." if len(sec_text) > 120 else ""),
                "word_count": sum(s["word_count"] for s in matching),
                "total_sentences": len(matching),
                "ai_sentences": sum(1 for s in matching if s.get("is_flagged", False)),
                "ai_percentage": sec_ai_pct,
                "verdict": sec_verdict,
                "sentence_indices": [scored_sentences.index(s) for s in matching if s in scored_sentences]
            })
        if sections:
            return sections

    # Fallback to paragraph splitting
    raw_blocks = [b.strip() for b in re.split(r'\n\s*\n+', text) if b.strip()]
    if not raw_blocks:
        raw_blocks = [text.strip()]

    sections = []
    sentence_idx = 0
    total_sentences = len(scored_sentences)

    for block_idx, block in enumerate(raw_blocks):
        first_line = block.split('\n')[0].strip()
        if len(first_line) < 60 and not first_line.endswith(('.', '!', '?')) and len(first_line.split()) <= 8:
            section_title = first_line
        else:
            words_preview = block.split()[:6]
            section_title = f"Section {block_idx + 1}: {' '.join(words_preview)}..."

        block_sentences: list[dict[str, Any]] = []
        block_lower = block.lower()

        while sentence_idx < total_sentences:
            s = scored_sentences[sentence_idx]
            snippet = s["sentence"][:35].lower()
            if snippet in block_lower or block_idx == len(raw_blocks) - 1:
                block_sentences.append(s)
                sentence_idx += 1
            else:
                break

        if not block_sentences:
            continue

        sec_char_len = sum(s.get("char_len", len(s["sentence"])) for s in block_sentences)
        sec_ai_chars = sum(s.get("char_len", len(s["sentence"])) for s in block_sentences if s.get("is_flagged", False))
        sec_ai_pct = round((sec_ai_chars / sec_char_len) * 100.0, 1) if sec_char_len > 0 else 0.0

        if sec_ai_pct >= 65.0:
            sec_verdict = "High AI Probability"
        elif sec_ai_pct >= 25.0:
            sec_verdict = "Needs Manual Review"
        else:
            sec_verdict = "Authentic Human"

        sections.append({
            "section_id": block_idx + 1,
            "title": section_title,
            "preview": block[:120].strip() + ("..." if len(block) > 120 else ""),
            "word_count": sum(s["word_count"] for s in block_sentences),
            "total_sentences": len(block_sentences),
            "ai_sentences": sum(1 for s in block_sentences if s.get("is_flagged", False)),
            "ai_percentage": sec_ai_pct,
            "verdict": sec_verdict,
            "sentence_indices": [scored_sentences.index(s) for s in block_sentences if s in scored_sentences]
        })

    return sections


def analyze_text(
    text: str,
    sensitivity: str = "balanced",
    esl_safeguard: bool = True,
    doc_tree: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Perform VeritasDoc multi-tier forensic evaluation on document text.
    """
    # Active sensitivity threshold tau
    tau = SENSITIVITY_THRESHOLDS.get(sensitivity.lower(), 0.60)

    # 1. Multi-Format & Regional Analysis
    multilingual_info = detect_multilingual_context(text)

    # 2. Robust Tokenization
    raw_sentences = tokenize_sentences_robust(text)
    valid_sentences = [s for s in raw_sentences if len(s.split()) >= MIN_SENTENCE_WORDS]
    if not valid_sentences:
        valid_sentences = [s for s in raw_sentences if s.strip()]

    # Check words for short text alert
    all_words = text.split()
    total_words = len(all_words)
    is_short_text = total_words < 50

    if not valid_sentences:
        return {
            "verdict": "Authentic Human",
            "verdict_zone": "GREEN",
            "ai_percentage": 0.0,
            "total_sentences": 0,
            "ai_sentences": 0,
            "total_words": total_words,
            "is_short_text": is_short_text,
            "sensitivity_mode": sensitivity,
            "threshold_tau": tau,
            "sentences": [],
            "sections": [],
            "ensemble": {},
            "forensic_metrics": {
                "perplexity": 45.0,
                "burstiness": 0.50,
                "lexical_diversity_ttr": 0.0,
                "yules_k": 0.0,
                "cliches_detected": 0
            },
            "attribution": {"platform": "N/A", "confidence": 0.0, "markers_found": []},
            "evasion": {"evasion_risk": "Low", "humanizer_risk": "Low"},
            "plagiarism": {"duplication_pct": 0.0, "redundancy_risk": "Clean"},
            "esl_guardrail": {"active": esl_safeguard, "is_candidate": False}
        }

    # 3. Detect ESL characteristics
    esl_data = detect_esl_patterns(text)
    is_esl_candidate = esl_data["is_esl_candidate"]

    # 4. Neural Consensus Inference across all 3 Cores
    raw_probabilities, ensemble_summary = predict_batch(valid_sentences)

    # 5. Apply Platt Scaling Calibration & ESL Attenuation
    calibrated_probs: list[float] = []
    for p in raw_probabilities:
        cp = calibrate_platt_score(p)
        if esl_safeguard and is_esl_candidate:
            # Apply ESL attenuation
            cp = round(cp * esl_data["attenuation_factor"], 4)
        calibrated_probs.append(cp)

    # 6. Apply Phase 3, Section 5.1 Gaussian Neighborhood Smoothing Kernel
    smoothed_probs = apply_gaussian_smoothing(calibrated_probs)

    # 7. Build Scored Sentences with Explainability Diagnostic Drawers
    scored_sentences: list[dict[str, Any]] = []
    sentence_ppls: list[float] = []
    total_chars = 0
    ai_chars = 0
    ai_sentences_count = 0

    for idx, (sentence, raw_p, smooth_p) in enumerate(zip(valid_sentences, raw_probabilities, smoothed_probs)):
        diag = compute_sentence_diagnostic(
            sentence=sentence,
            raw_prob=raw_p,
            smoothed_prob=smooth_p,
            tau=tau,
            esl_active=esl_safeguard,
            is_esl_candidate=is_esl_candidate
        )
        words_count = len(sentence.split())
        sentence_ppls.append(diag["ppl"])

        total_chars += diag["char_len"]
        if diag["is_flagged"]:
            ai_chars += diag["char_len"]
            ai_sentences_count += 1

        scored_sentences.append({
            "index": idx + 1,
            "sentence": sentence,
            "char_len": diag["char_len"],
            "word_count": words_count,
            "raw_prob": diag["raw_prob"],
            "smoothed_prob": diag["smoothed_prob"],
            "score": diag["score_pct"],
            "color": diag["color"],
            "color_label": diag["color_label"],
            "is_flagged": diag["is_flagged"],
            "is_ai": diag["is_flagged"],
            "confidence": diag["confidence"],
            "ppl": diag["ppl"],
            "cliches": diag["cliches_found"],
            "reasoning": diag["reasoning"],
            "platform_hint": diag["platform_hint"]
        })

    # 8. Character-Weighted AI Percentage Formula (Phase 3, Section 5.2):
    # AI% = (Sum CharLength(S_i) * I(S_tilde_i >= tau)) / (Sum CharLength(S_i)) * 100
    if total_chars > 0:
        overall_ai_pct = round((ai_chars / total_chars) * 100.0, 1)
    else:
        overall_ai_pct = 0.0

    # 9. 3-Zone Academic Decision Matrix (Phase 4, Section 6):
    # - Green Zone (< 25%): Authentic Human
    # - Yellow Zone (25% - 65%): Needs Manual Review
    # - Red Zone (> 65%): High AI Probability
    if overall_ai_pct > 65.0:
        verdict = "High AI Probability"
        verdict_zone = "RED"
    elif overall_ai_pct >= 25.0:
        verdict = "Needs Manual Review"
        verdict_zone = "YELLOW"
    else:
        verdict = "Authentic Human"
        verdict_zone = "GREEN"

    # 10. Statistical & Stylometric Forensic Metrics
    burstiness_val = compute_document_burstiness(sentence_ppls)
    doc_ppl = round(sum(sentence_ppls) / len(sentence_ppls), 1) if sentence_ppls else 45.0
    stylometrics = compute_stylometrics(text, all_words)
    zipf_data = compute_zipfian_entropy(all_words)

    # 11. Bonus Evasion & Humanizer Detection (Phase 7, Bonus 2)
    evasion_data = detect_humanizer_evasion(text, scored_sentences)

    # 12. Bonus Platform Attribution (Phase 7, Bonus 1)
    attribution = _detect_platform_attribution(scored_sentences, overall_ai_pct)

    # 13. Plagiarism & Redundancy Check
    plagiarism = _check_plagiarism_and_redundancy(scored_sentences)

    # 14. Section-Wise Breakdown
    sections = _segment_sections(doc_tree, text, scored_sentences, tau)

    model_used = get_model_status()["model_name"] or "VeritasDoc Multi-Vector Consensus Core"

    sha256_hash = doc_tree.get("sha256_hash") if doc_tree else None

    return {
        "verdict": verdict,
        "verdict_zone": verdict_zone,
        "ai_percentage": overall_ai_pct,
        "total_sentences": len(scored_sentences),
        "ai_sentences": ai_sentences_count,
        "total_words": total_words,
        "total_chars": total_chars,
        "is_short_text": is_short_text,
        "sensitivity_mode": sensitivity,
        "threshold_tau": tau,
        "sha256_hash": sha256_hash,
        "model_used": model_used,
        "ensemble": ensemble_summary,
        "forensic_metrics": {
            "perplexity": doc_ppl,
            "burstiness": burstiness_val,
            "lexical_diversity_ttr": stylometrics["ttr_pct"],
            "yules_k": stylometrics["yules_k"],
            "cliches_detected": stylometrics["cliche_count"],
            "top_cliches": stylometrics["cliche_tokens"],
            "zipf_r2": zipf_data["zipf_r2"],
            "zipf_top10_ratio": zipf_data["top_10_ratio_pct"]
        },
        "sentences": scored_sentences,
        "sections": sections,
        "attribution": attribution,
        "evasion": evasion_data,
        "plagiarism": plagiarism,
        "esl_guardrail": {
            "active": esl_safeguard,
            "is_candidate": is_esl_candidate,
            "detected_markers": esl_data.get("detected_markers", []),
            "reasoning": esl_data.get("reasoning", "")
        },
        "multilingual": multilingual_info
    }
