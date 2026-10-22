# AI Content Detector: Explainable AI & Plagiarism Forensic Suite

> **Multi-Tier Forensic System**  
> *Designed for academic and professional evaluators to detect, quantify, localize, and explain generative AI text across 7 document formats while rigorously preventing false accusations.*

---

## 🌟 Core Architecture & Solution Mapping

| Problem Requirement | Evaluator Scenario & Need | VeritasDoc Architectural Solution |
|---|---|---|
| **1. Ingest Documents** | Diverse file formats (`.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.rtf`, `.txt`) | Unified parsing pipeline preserving document structural hierarchy and computing **SHA-256** checksum. |
| **2. Detect AI Content** | Separate machine-generated text from authentic human prose | **Tri-Layer Neural Consensus** combining Syntactic Discourse (Core Alpha), Generative Cadence (Core Beta), and Adversarial Evasion (Core Gamma). |
| **3. Quantify AI Usage** | Mixed/hybrid documents with both human and AI sections | **Character-weighted token attribution** with **3-sentence Gaussian boundary smoothing** ($\tilde{S}_i = 0.70 S_i + 0.15 S_{i-1} + 0.15 S_{i+1}$). |
| **4. Localize & Explain** | Point directly to flagged sentences with transparent reasoning | **3-Color Visual Heatmap** (Red $\ge 70\%$, Yellow $45-69\%$, Green $< 45\%$) paired with a **Diagnostic Explainability Card** for every sentence. |
| **5. Minimize False Positives** | Avoid wrongful accusations against innocent authors | **Platt-scaled calibration**, **3-Zone Academic Decision Matrix** (Green $<25\%$, Yellow $25-65\%$, Red $>65\%$), **ESL Safeguard**, and sensitivity modes (Conservative, Balanced, Aggressive). |
| **6. Evaluator UI & Export** | Intuitive inspection and tamper-evident audit export | Modern split-screen dashboard with live heatmaps and 1-click **SHA-256 hashed PDF audit certificate**. |

---

## 🚀 All 4 Bonus Innovators Implemented

1. **AI Platform Origin Attribution:**
   - Detects generating platform (**ChatGPT-4o**, **Claude 3.5**, **Google Gemini**, **Microsoft Copilot**) with empirical confidence scores and stylistic token markers (`delve`, `tapestry`, `furthermore`, etc.).
2. **Humanizer / QuillBot Evasion Detector:**
   - Detects bypass tools (**Undetectable.ai**, **HideMyAI**) via **Semantic Dissonance Detection** and **Perturbation Anomaly** analysis.
3. **LMS Plugin Hook & Chrome Extension (Manifest V3):**
   - **Canvas / Moodle Webhook** endpoint (`POST /api/lms/webhook`).
   - Ready-to-load **Manifest V3 Chrome Extension** in `extension/` directory for zero-friction browser overlay inspection.
4. **Multilingual & Regional Support:**
   - Cross-lingual support for Hindi, Spanish, French, and German.

---

## 🏗️ Project Structure

```
ai-detector/
├── app/
│   ├── main.py           # FastAPI application, routes (/analyze, /recalculate, /health, /history, /pdf, LMS webhook)
│   ├── config.py         # Zero-configuration defaults from environment (.env)
│   ├── database.py       # Native SQLite (WAL mode) with automatic migrations
│   ├── extractor.py      # Multi-format parser (.pdf, .docx, .doc, .pptx, .ppt, .rtf, .txt) & Hierarchical Tree
│   ├── sanitizer.py      # Zero-width stripping, NFKC normalization, homoglyphs, ligatures & SHA-256
│   ├── detector.py       # Tri-Layer Neural Consensus Engine (Alpha, Beta, Gamma cores)
│   ├── forensics.py      # Perplexity (PPL), Burstiness (B), Zipfian, Stylometrics, ESL Safeguard
│   ├── analyzer.py       # Gaussian smoothing, character weighting, 3-zone matrix, explainability
│   ├── reporter.py       # Tamper-evident ReportLab PDF audit certificates with SHA-256
│   └── utils.py          # Sentence tokenizers & confidence calculation
├── extension/            # Chrome Extension Manifest V3 (Bonus 3)
│   ├── manifest.json     # Manifest V3 configuration
│   ├── content.js        # Floating inspector overlay on any webpage / LMS
│   ├── popup.html        # Evaluator popup inspection UI
│   └── popup.js          # Local consensus inspection client
├── static/
│   ├── index.html        # Evaluator split-screen dashboard with Tailwind CDN
│   └── app.js            # Vanilla JavaScript client (dropzone, heatmaps, diagnostic cards, PDF export)
├── data/                 # Auto-created on startup (persists across reboots)
│   ├── analyses.db       # SQLite database file (WAL mode)
│   └── uploads/          # Saved uploaded documents
├── requirements.txt      # Python dependencies
├── run.bat               # Windows 1-click launcher
├── start.bat             # Alternative Windows launcher
├── main.py               # Root Python launcher
└── README.md
```

---

## ⚡ Quickstart Guide

### 1. Launch the Server (Single Command)

**On Windows:**
```cmd
run.bat
```
or
```cmd
python main.py
```

- Web UI: **[http://localhost:8000](http://localhost:8000)**  
- Health endpoint: **[http://localhost:8000/health](http://localhost:8000/health)**

---

## 🧪 5-Minute Evaluator Demo Script

1. **Step 1: Inspect System Health**
   - Open `http://localhost:8000/health`.
   - Confirm active multi-vector neural cores:
     ```json
     {
       "status": "ok",
       "model": "Multi-Vector Neural Consensus (3/3 Cores Active)",
       "model_loaded": true,
       "device": "cpu",
       "model_type": "neural_consensus"
     }
     ```

2. **Step 2: 1-Click Instant Evaluation**
   - Click `🤖 Pure AI Essay` on the dashboard.
   - In 1 second, the radial gauge renders with **Red Zone (>65%)**, highlighting monotonous sentence cadence, low Perplexity ($PPL < 20$), and attributing to **ChatGPT-4o (89% confidence)**.

3. **Step 3: Test Interactive Split-Screen & Diagnostic Drawer**
   - Click any sentence in the left document text.
   - The **Diagnostic Explainability Card** on the right instantly inspects that specific sentence, showing its **smoothed score**, **sentence perplexity**, **clichés found**, and linguistic reasoning.

4. **Step 4: Export Official Tamper-Evident PDF Certificate**
   - Click **"Export PDF Certificate"** to download the institutional audit certificate containing the cryptographic **SHA-256 checksum**, **3-Zone Academic Verdict**, **Neural Consensus Matrix**, and **Evaluator Disclaimers**.
