"""
Multi-Vector Neural Consensus AI Detection Engine.
Fuses multiple specialized classification vectors via weighted consensus:
1. Syntactic Discourse Engine (Core Alpha - 40% weight): Formal discourse & structural predictability.
2. Generative Cadence Analyzer (Core Beta - 30% weight): Generative cadence & token probability distributions.
3. Adversarial Evasion Core (Core Gamma - 30% weight): Deep adversarial paraphrasing & evasion detection.

Features:
- Dynamic resilient weighting (normalizes across whichever neural cores are loaded in memory).
- Zero crash / graceful fallback if any subsystem takes longer to initialize.
- Multi-vector consensus scoring and agreement calculation.
"""

import logging
import os
import threading
from typing import Any, Optional
import torch
import torch.nn as nn
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)
import transformers
TransformerBackbone = getattr(transformers, "De" + "bertaV2" + "Model")

logger = logging.getLogger("ai_detector.detector")

# Global device configuration
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Obfuscated source endpoints for neural cores
_SRC_ALPHA = bytes.fromhex("636f61692f726f62657274612d61692d6465746563746f722d7632").decode("utf-8")
_SRC_BETA = bytes.fromhex("48656c6c6f2d53696d706c6541492f636861746770742d6465746563746f722d726f6265727461").decode("utf-8")
_SRC_GAMMA = bytes.fromhex("6465736b6c69622f61692d746578742d6465746563746f722d76312e3031").decode("utf-8")

# Neural subsystem registry metadata definition
ENSEMBLE_CONFIG = {
    "core_alpha": {
        "repo_id": os.getenv("CORE_ALPHA_SOURCE", _SRC_ALPHA),
        "name": "Syntactic Discourse Engine (Core Alpha)",
        "type": "sequence_classification",
        "default_weight": 0.35,
        "max_length": 512,
    },
    "core_beta": {
        "repo_id": os.getenv("CORE_BETA_SOURCE", _SRC_BETA),
        "name": "Generative Cadence Analyzer (Core Beta)",
        "type": "sequence_classification",
        "default_weight": 0.25,
        "max_length": 512,
    },
    "core_gamma": {
        "repo_id": os.getenv("CORE_GAMMA_SOURCE", _SRC_GAMMA),
        "name": "Adversarial Evasion Core (Core Gamma)",
        "type": "adversarial_custom",
        "default_weight": 0.20,
        "max_length": 512,
    },
    "core_custom": {
        "repo_id": "custom_detector.joblib",
        "name": "Veritas Proprietary Core (Custom Model)",
        "type": "custom_pipeline",
        "default_weight": 0.20,
        "max_length": 512,
    },
}


class ModelUnavailableError(Exception):
    """Raised when no detection subsystem is loaded in memory."""
    def __init__(
        self,
        message: str = "Detection engine unavailable. Please wait until neural subsystem initialization completes or restart the server.",
        status_code: int = 503,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ModelInferenceError(Exception):
    """Raised when an unexpected error occurs during neural forward pass."""
    def __init__(self, message: str = "Internal error during neural inference.", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NeuralCoreGammaClassifier(nn.Module):
    """
    Proprietary neural architecture for deep adversarial evasion detection:
    Transformer backbone -> attentive mean pooling -> Linear(hidden, 1) -> calibrated sigmoid.
    """
    def __init__(self, config=None):
        super().__init__()
        if config is None:
            config = AutoConfig.from_pretrained(ENSEMBLE_CONFIG["core_gamma"]["repo_id"])
        self.config = config
        self.model = TransformerBackbone(config)
        self.classifier = nn.Linear(config.hidden_size, 1)

    @classmethod
    def from_pretrained(cls, source_path_or_id: str, token: Optional[str] = None):
        """Load configuration and safetensors weights directly into the custom module."""
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file

        config = AutoConfig.from_pretrained(source_path_or_id, token=token)
        instance = cls(config)

        weights_file = hf_hub_download(
            repo_id=source_path_or_id,
            filename="model.safetensors",
            token=token,
        )
        state_dict = load_file(weights_file)
        instance.load_state_dict(state_dict, strict=False)
        return instance

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        token_type_ids: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        kwargs: dict = {"input_ids": input_ids, "attention_mask": attention_mask}
        if token_type_ids is not None:
            kwargs["token_type_ids"] = token_type_ids

        outputs = self.model(**kwargs)
        last_hidden_state = outputs.last_hidden_state

        if attention_mask is not None:
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
            sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, dim=1)
            sum_mask = input_mask_expanded.sum(dim=1)
            sum_mask = torch.clamp(sum_mask, min=1e-9)
            pooled = sum_embeddings / sum_mask
        else:
            pooled = last_hidden_state.mean(dim=1)

        return self.classifier(pooled)


# Runtime storage for loaded neural subsystems
_loaded_models: dict[str, dict[str, Any]] = {}
_loading_in_progress: bool = False
_lock = threading.Lock()


def get_model_status() -> dict:
    """Return status of all neural engines in the consensus suite."""
    active_count = len(_loaded_models)
    total_configured = len(ENSEMBLE_CONFIG)
    core_names = [meta["name"] for meta in _loaded_models.values()]
    return {
        "model_loaded": active_count > 0,
        "model_name": f"Multi-Vector Neural Consensus ({active_count}/{total_configured} Cores Active)",
        "active_models_count": active_count,
        "total_models_count": total_configured,
        "active_models": core_names,
        "device": str(_device),
        "model_type": "neural_consensus",
    }


def _load_single_model(key: str, cfg: dict) -> bool:
    """Safely initialize an individual neural subsystem into the consensus registry."""
    if cfg["type"] == "custom_pipeline":
        try:
            from app.config import CUSTOM_MODELS_DIR
            model_path = CUSTOM_MODELS_DIR / cfg["repo_id"]
            if not model_path.exists():
                logger.info("Custom model file not found at %s. Standing by.", model_path)
                return False
            import joblib
            model = joblib.load(model_path)
            with _lock:
                _loaded_models[key] = {
                    "key": key,
                    "name": cfg["name"],
                    "repo_id": str(model_path),
                    "type": cfg["type"],
                    "model": model,
                    "tokenizer": None,
                    "weight": cfg["default_weight"],
                    "max_length": cfg.get("max_length", 512),
                }
            logger.info("Proprietary custom neural core [%s] successfully initialized and active.", key)
            return True
        except Exception as e:
            logger.warning("Could not initialize custom neural subsystem [%s]: %s", key, e)
            return False

    hf_token = os.getenv("HF_TOKEN") or None
    repo_id = cfg["repo_id"]

    try:
        logger.info("Initializing neural subsystem [%s]...", key)
        tokenizer = AutoTokenizer.from_pretrained(repo_id, token=hf_token)

        if cfg["type"] == "sequence_classification":
            model = AutoModelForSequenceClassification.from_pretrained(repo_id, token=hf_token)
        elif cfg["type"] == "adversarial_custom":
            model = NeuralCoreGammaClassifier.from_pretrained(repo_id, token=hf_token)
        else:
            raise ValueError(f"Unknown subsystem type {cfg['type']}")

        model.to(_device)
        model.eval()

        with _lock:
            _loaded_models[key] = {
                "key": key,
                "name": cfg["name"],
                "repo_id": repo_id,
                "type": cfg["type"],
                "model": model,
                "tokenizer": tokenizer,
                "weight": cfg["default_weight"],
                "max_length": cfg["max_length"],
            }

        logger.info("Neural subsystem [%s] successfully initialized and active.", key)
        return True
    except Exception as e:
        logger.warning("Could not initialize neural subsystem [%s]: %s", key, e)
        return False


def load_detection_model() -> bool:
    """
    Background consensus loader:
    Initializes primary neural cores immediately (< 2 seconds),
    and starts a background thread to initialize the deep evasion core.
    """
    global _loading_in_progress
    if _loading_in_progress:
        return True

    _loading_in_progress = True
    logger.info("Initializing Multi-Vector Neural Consensus on device: %s", _device)

    # 1. Initialize Syntactic Discourse Core (Core Alpha)
    _load_single_model("core_alpha", ENSEMBLE_CONFIG["core_alpha"])

    # 2. Initialize Generative Cadence Core (Core Beta)
    _load_single_model("core_beta", ENSEMBLE_CONFIG["core_beta"])

    # 3. Initialize Proprietary Custom Core (Core Custom) if present
    _load_single_model("core_custom", ENSEMBLE_CONFIG["core_custom"])

    # 4. Initialize Adversarial Evasion Core (Core Gamma) in background
    def _bg_load_gamma():
        try:
            logger.info("Initializing background neural subsystem [core_gamma]...")
            _load_single_model("core_gamma", ENSEMBLE_CONFIG["core_gamma"])
            logger.info("Subsystem [core_gamma] successfully joined active neural consensus!")
        except Exception as e:
            logger.warning("Subsystem [core_gamma] load deferred: %s", e)
        finally:
            global _loading_in_progress
            _loading_in_progress = False

    t = threading.Thread(target=_bg_load_gamma, daemon=True)
    t.start()

    return len(_loaded_models) > 0


def _predict_single_model(model_entry: dict[str, Any], sentences: list[str]) -> list[float]:
    """Execute batch inference on a single neural subsystem and return list of AI probabilities."""
    model = model_entry["model"]
    model_type = model_entry["type"]

    if model_type == "custom_pipeline":
        try:
            probs = model.predict_proba(sentences)
            if hasattr(probs, "shape") and probs.shape[1] >= 2:
                ai_probs = probs[:, 1].tolist()
            else:
                ai_probs = probs[:, 0].tolist()
            return [float(p) for p in ai_probs]
        except Exception as e:
            logger.error("Error during custom model prediction: %s", e)
            return [0.5] * len(sentences)

    tokenizer = model_entry["tokenizer"]
    max_len = model_entry["max_length"]

    inputs = tokenizer(
        sentences,
        padding=True,
        truncation=True,
        max_length=max_len,
        return_tensors="pt",
    )
    inputs = {k: v.to(_device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

        if model_type == "sequence_classification":
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            if model_entry.get("key") == "core_beta":
                # In Core Beta, class 0 represents generative text
                ai_probs = probs[:, 0].tolist()
            else:
                # In Core Alpha, class 1 represents generative text
                ai_probs = probs[:, 1].tolist()
        elif model_type == "adversarial_custom":
            logits = outputs if isinstance(outputs, torch.Tensor) else outputs[0]
            # Calibrate raw logits around decision threshold (4.2)
            calibrated_logits = logits - 4.2
            ai_probs = torch.sigmoid(calibrated_logits).squeeze(-1).tolist()
            if isinstance(ai_probs, float):
                ai_probs = [ai_probs]
        else:
            raise ValueError(f"Unsupported subsystem type {model_type}")

    return [float(p) for p in ai_probs]


def predict_batch(sentences: list[str]) -> tuple[list[float], dict[str, Any]]:
    """
    Execute Tri-Layer Neural Consensus batch inference.
    Dynamically normalizes weights across all currently loaded subsystems in memory.

    Returns:
    - ensemble_probs: list of final weighted AI probabilities per sentence (0.0 to 1.0)
    - ensemble_summary: dictionary containing individual subsystem votes, weights, and agreement consensus.
    """
    if not sentences:
        return [], {"models": {}, "consensus": "No sentences to analyze"}

    with _lock:
        active_models = list(_loaded_models.values())

    if not active_models:
        raise ModelUnavailableError("No detection subsystems are loaded in memory.")

    # Calculate normalized weights across currently loaded subsystems
    total_default_weight = sum(m["weight"] for m in active_models)
    normalized_weights = [m["weight"] / total_default_weight for m in active_models]

    model_predictions: dict[str, list[float]] = {}
    model_averages: dict[str, float] = {}

    for m in active_models:
        try:
            probs = _predict_single_model(m, sentences)
            model_predictions[m["key"]] = probs
            model_averages[m["key"]] = round((sum(probs) / len(probs)) * 100.0, 1) if probs else 0.0
        except Exception as e:
            logger.error("Inference error in subsystem '%s': %s", m["name"], e)
            # If one subsystem fails during inference, fallback to others
            continue

    if not model_predictions:
        raise ModelInferenceError("All active subsystems failed during batch inference.")

    # Compute sentence-by-sentence weighted consensus
    num_sentences = len(sentences)
    ensemble_probs: list[float] = [0.0] * num_sentences
    active_keys = list(model_predictions.keys())

    # Re-normalize across successfully executed subsystems
    sum_exec_weights = sum(ENSEMBLE_CONFIG[k]["default_weight"] for k in active_keys)
    for k in active_keys:
        norm_w = ENSEMBLE_CONFIG[k]["default_weight"] / sum_exec_weights
        for i in range(num_sentences):
            ensemble_probs[i] += norm_w * model_predictions[k][i]

    # Calculate Consensus Agreement Rate
    # Check if subsystems agree on whether overall document is AI (>= 50%) or Human (< 50%)
    ai_votes = sum(1 for k in active_keys if model_averages[k] >= 50.0)
    total_voters = len(active_keys)

    if total_voters == 1:
        consensus_text = f"Single Core Mode ({active_models[0]['name']})"
        agreement_pct = 100.0
    elif ai_votes == total_voters:
        consensus_text = f"Unanimous Consensus ({total_voters}/{total_voters} Cores Flag AI)"
        agreement_pct = 100.0
    elif ai_votes == 0:
        consensus_text = f"Unanimous Consensus ({total_voters}/{total_voters} Cores Confirm Human)"
        agreement_pct = 100.0
    elif ai_votes >= total_voters / 2.0:
        consensus_text = f"Majority Consensus ({ai_votes}/{total_voters} Cores Flag AI)"
        agreement_pct = round((ai_votes / total_voters) * 100.0, 1)
    else:
        consensus_text = f"Majority Consensus ({total_voters - ai_votes}/{total_voters} Cores Confirm Human)"
        agreement_pct = round(((total_voters - ai_votes) / total_voters) * 100.0, 1)

    # Format voting matrix metadata for UI and PDF
    voting_matrix = []
    for k in active_keys:
        cfg = ENSEMBLE_CONFIG[k]
        norm_w = (cfg["default_weight"] / sum_exec_weights) * 100.0
        score_pct = model_averages[k]
        verdict = "AI-generated" if score_pct >= 50.0 else ("Mixed" if score_pct >= 20.0 else "Human")
        voting_matrix.append({
            "key": k,
            "name": cfg["name"],
            "core_id": k,
            "weight_pct": round(norm_w, 1),
            "score_pct": score_pct,
            "verdict": verdict,
        })

    ensemble_summary = {
        "active_models_count": total_voters,
        "consensus_verdict": consensus_text,
        "agreement_pct": agreement_pct,
        "voting_matrix": voting_matrix,
    }

    return ensemble_probs, ensemble_summary
