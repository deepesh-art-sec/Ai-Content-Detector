# VeritasDoc Custom Model Integration Guide

This directory holds custom proprietary models integrated into the VeritasDoc Multi-Vector Neural Consensus.

## Architecture & Integration (Non-Destructive)
- **Zero Pretrained Model Disruption**: The 3 core neural models (`core_alpha`, `core_beta`, `core_gamma`) remain 100% active and untouched.
- **Dynamic Consensus Re-weighting**: When `custom_detector.joblib` exists, the detector automatically initializes `core_custom` and blends it into the consensus:
  - `core_alpha` (Discourse & Attention): 35% weight
  - `core_beta` (Generative Cadence): 25% weight
  - `core_gamma` (Adversarial Evasion): 20% weight
  - `core_custom` (Proprietary Custom Engine): 20% weight

If `custom_detector.joblib` is removed or disabled, the system gracefully falls back to the 3 pretrained cores with zero downtime.

## How to Re-Train with Custom Data
1. Place custom AI text files (`.txt`) in `data/custom_dataset/ai/`.
2. Place custom Human text files (`.txt`) in `data/custom_dataset/human/`.
3. Run:
   ```bash
   python train_custom_model.py
   ```
4. The script fits the dual-vector morphological TF-IDF feature extractor + calibrated classifier, evaluates validation metrics, and writes:
   - `custom_models/custom_detector.joblib`
   - `custom_models/model_metadata.json`
5. Restart or reload the server — the custom model will be active in consensus immediately.
