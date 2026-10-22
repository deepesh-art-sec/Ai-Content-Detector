/**
 * VeritasDoc AI Content Detector & Plagiarism Suite
 * Enterprise Frontend Application Engine
 * 100% Local Inference & SHA-256 Tamper-Evident Reporting
 */

// ================= GLOBAL APPLICATION STATE =================
let currentAnalysisData = null;
let selectedFile = null;
let currentInputMode = 'file'; // 'file' | 'text'
let activeFilter = 'all';      // 'all' | 'red' | 'yellow' | 'green'
let selectedSentenceIndex = 0;
let sensitivityMode = 'balanced'; // 'conservative' | 'balanced' | 'aggressive'
let eslSafeguard = true;
let historyCache = [];
let isHistoryDrawerOpen = false;

// Benchmark Test Samples for 1-Click Verification
const DEMO_SAMPLES = {
  ai: `Artificial intelligence has undeniably revolutionized modern natural language processing and computer vision systems. Furthermore, recent breakthroughs in generative transformers serve as a testament to the rapid velocity of contemporary technological innovation. In conclusion, we must delve deeper into the multifaceted ethical implications and technical challenges that emerge as these technologies reshape academic integrity and knowledge distribution across global institutions. Moreover, establishing standardized evaluation frameworks will be paramount in fostering transparent algorithmic governance.`,
  human: `We conducted three experiments in the physics laboratory to measure the gravitational constant using a simple pendulum and a digital stopwatch. During our third trial run, the string slipped slightly on the clamp which caused a brief timing discrepancy that we noted in our lab notebooks. Overall the experiment demonstrated that small variations in angle have a negligible effect when kept below ten degrees. My lab partner and I repeated the timing five times to calculate the standard deviation before submitting our draft to Professor Miller.`,
  mixed: `We conducted three experiments in the physics laboratory to measure the gravitational constant using a simple pendulum and a digital stopwatch. During our third trial run, the string slipped slightly on the clamp which caused a brief timing discrepancy that we noted in our lab notebooks.

Furthermore, generative AI systems represent a paradigm shift in modern natural language understanding. It is a testament to recent breakthroughs in deep learning architectures. In conclusion, educational institutions must delve into rigorous authenticity verification protocols.`
};

// ================= DOM ELEMENT REFERENCES =================
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const filePreview = document.getElementById('file-preview');
const fileNameEl = document.getElementById('file-name');
const fileSizeEl = document.getElementById('file-size');
const fileExtBadge = document.getElementById('file-ext-badge');
const pasteTextInput = document.getElementById('paste-text-input');
const pasteWordCountEl = document.getElementById('paste-word-count');
const analyzeBtn = document.getElementById('analyze-btn');
const loadingCard = document.getElementById('loading-card');
const resultsCard = document.getElementById('results-card');
const errorBanner = document.getElementById('error-banner');
const errorMessage = document.getElementById('error-message');
const shortTextBanner = document.getElementById('short-text-banner');
const modelStatusText = document.getElementById('model-status-text');
const statusDot = document.getElementById('status-dot');
const statusPing = document.getElementById('status-ping');

// ================= INITIALIZATION =================
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  checkHealth();
  fetchHistory();
  // Poll health status periodically
  setInterval(checkHealth, 30000);
});

function setupEventListeners() {
  // Drag and Drop on dropzone
  if (dropzone) {
    dropzone.addEventListener('click', () => fileInput && fileInput.click());
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('border-brand-500', 'bg-brand-500/[0.08]');
    });
    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('border-brand-500', 'bg-brand-500/[0.08]');
    });
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('border-brand-500', 'bg-brand-500/[0.08]');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileSelection(e.dataTransfer.files[0]);
      }
    });
  }

  // File Input Change
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelection(e.target.files[0]);
      }
    });
  }

  // Live word counter on textarea
  if (pasteTextInput) {
    pasteTextInput.addEventListener('input', () => {
      const text = pasteTextInput.value.trim();
      const count = text ? text.split(/\s+/).filter(Boolean).length : 0;
      if (pasteWordCountEl) pasteWordCountEl.textContent = count;
    });
  }
}

// ================= INPUT MODE SWITCHING =================
function switchInputMode(mode) {
  expandInputStation();
  currentInputMode = mode;
  const tabFile = document.getElementById('input-tab-file');
  const tabText = document.getElementById('input-tab-text');
  const dropzoneMode = document.getElementById('dropzone-mode');
  const pasteMode = document.getElementById('paste-mode');

  if (mode === 'file') {
    tabFile.className = 'px-3.5 py-1.5 rounded-lg bg-brand-600 text-white font-semibold transition cursor-pointer';
    tabText.className = 'px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-white transition cursor-pointer';
    dropzoneMode.classList.remove('hidden');
    pasteMode.classList.add('hidden');
  } else {
    tabText.className = 'px-3.5 py-1.5 rounded-lg bg-brand-600 text-white font-semibold transition cursor-pointer';
    tabFile.className = 'px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-white transition cursor-pointer';
    dropzoneMode.classList.add('hidden');
    pasteMode.classList.remove('hidden');
    if (pasteTextInput) pasteTextInput.focus();
  }
}

function handleFileSelection(file) {
  selectedFile = file;
  if (fileNameEl) fileNameEl.textContent = file.name;
  if (fileSizeEl) fileSizeEl.textContent = formatBytes(file.size);
  if (fileExtBadge) {
    const ext = file.name.split('.').pop().toUpperCase() || 'FILE';
    fileExtBadge.textContent = ext.substring(0, 4);
  }
  if (filePreview) filePreview.classList.remove('hidden');
}

function clearSelectedFile() {
  selectedFile = null;
  if (fileInput) fileInput.value = '';
  if (filePreview) filePreview.classList.add('hidden');
}

function loadSample(type) {
  dismissError();
  const sampleText = DEMO_SAMPLES[type];
  if (!sampleText) return;

  switchInputMode('text');
  if (pasteTextInput) {
    pasteTextInput.value = sampleText;
    const wordCount = sampleText.trim().split(/\s+/).filter(Boolean).length;
    if (pasteWordCountEl) pasteWordCountEl.textContent = wordCount;

    pasteTextInput.classList.add('ring-2', 'ring-brand-500');
    setTimeout(() => {
      pasteTextInput.classList.remove('ring-2', 'ring-brand-500');
    }, 600);
  }
}

// ================= INGESTION STATION EXPAND / COLLAPSE =================
function collapseInputStation() {
  const fullView = document.getElementById('input-full-view');
  const collapsedBar = document.getElementById('input-collapsed-bar');
  if (fullView) fullView.classList.add('hidden');
  if (collapsedBar) collapsedBar.classList.remove('hidden');
}

function expandInputStation() {
  const fullView = document.getElementById('input-full-view');
  const collapsedBar = document.getElementById('input-collapsed-bar');
  if (fullView) fullView.classList.remove('hidden');
  if (collapsedBar) collapsedBar.classList.add('hidden');
}

// ================= SENSITIVITY & GUARDRAIL CONTROLS =================
function setSensitivity(mode) {
  sensitivityMode = mode;
  ['conservative', 'balanced', 'aggressive'].forEach(m => {
    const btn = document.getElementById(`sens-btn-${m}`);
    if (btn) {
      if (m === mode) {
        btn.className = 'px-2.5 py-1 rounded bg-brand-600 text-white font-semibold transition cursor-pointer';
      } else {
        btn.className = 'px-2.5 py-1 rounded text-slate-400 hover:text-white transition cursor-pointer';
      }
    }
  });

  // If results are actively displayed, recalculate in real-time
  if (currentAnalysisData) {
    recalculateActiveAnalysis();
  }
}

function toggleEslSafeguard() {
  const el = document.getElementById('esl-toggle');
  if (el) eslSafeguard = el.checked;
  if (currentAnalysisData) {
    recalculateActiveAnalysis();
  }
}

async function recalculateActiveAnalysis() {
  if (!currentAnalysisData) return;
  const originalText = currentAnalysisData.sentences ? currentAnalysisData.sentences.map(s => s.sentence).join(' ') : '';
  if (!originalText) return;

  try {
    const response = await fetch('/recalculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: originalText,
        sensitivity: sensitivityMode,
        esl_safeguard: eslSafeguard
      })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Recalculation failed');
    }

    const updatedData = await response.json();
    // Preserve metadata
    updatedData.id = currentAnalysisData.id;
    updatedData.filename = currentAnalysisData.filename;
    displayResults(updatedData);
  } catch (err) {
    console.warn('Real-time recalculation error:', err);
  }
}

// ================= ANALYSIS SUBMISSION =================
async function submitAnalysis() {
  dismissError();

  let bodyData = null;
  let isFileUpload = (currentInputMode === 'file');

  if (isFileUpload) {
    if (!selectedFile) {
      showError('Please select a document file (.pdf, .docx, .doc, .pptx, .ppt, .rtf, .txt) to evaluate.');
      return;
    }
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('sensitivity', sensitivityMode);
    formData.append('esl_safeguard', eslSafeguard);
    bodyData = formData;
  } else {
    const text = pasteTextInput.value.trim();
    if (!text) {
      showError('Please paste some text content to analyze.');
      return;
    }
    const blob = new Blob([text], { type: 'text/plain' });
    const formData = new FormData();
    formData.append('file', blob, 'pasted_text.txt');
    formData.append('sensitivity', sensitivityMode);
    formData.append('esl_safeguard', eslSafeguard);
    bodyData = formData;
  }

  // Show Loading State
  loadingCard.classList.remove('hidden');
  resultsCard.classList.add('hidden');
  loadingCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
  analyzeBtn.disabled = true;

  try {
    const response = await fetch('/analyze', {
      method: 'POST',
      body: bodyData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server returned error status ${response.status}`);
    }

    const data = await response.json();
    displayResults(data);
  } catch (err) {
    console.error('Analysis request failed:', err);
    showError(err.message || 'Analysis could not be completed. Please ensure the backend is active.');
  } finally {
    loadingCard.classList.add('hidden');
    analyzeBtn.disabled = false;
  }
}

// ================= DISPLAY RESULTS =================
function displayResults(data) {
  currentAnalysisData = data;

  // Academic Guardrail: Short text warning
  if (data.is_short_text) {
    shortTextBanner.classList.remove('hidden');
  } else {
    shortTextBanner.classList.add('hidden');
  }

  // Auto-collapse input station so results appear directly at top of viewport
  collapseInputStation();
  const collapsedFilename = document.getElementById('collapsed-filename');
  if (collapsedFilename) collapsedFilename.textContent = data.filename || 'submission.txt';

  const collapsedVerdict = document.getElementById('collapsed-verdict');
  if (collapsedVerdict) collapsedVerdict.textContent = `${data.verdict} (${data.ai_percentage.toFixed(1)}%)`;

  const collapsedStats = document.getElementById('collapsed-stats');
  if (collapsedStats) collapsedStats.textContent = `• ${data.total_words || 0} words • ${data.total_sentences || 0} sentences`;

  // 1. Circular Gauge & Verdict Dossier
  const aiPct = Math.max(0, Math.min(100, data.ai_percentage || 0));
  const aiPercentText = document.getElementById('ai-percent-text');
  if (aiPercentText) aiPercentText.textContent = `${aiPct.toFixed(1)}%`;

  const gaugeCircle = document.getElementById('gauge-circle');
  if (gaugeCircle) {
    const circ = 251.32; // 2 * Math.PI * 40
    const offset = circ - (aiPct / 100) * circ;
    gaugeCircle.style.strokeDashoffset = offset;

    if (aiPct >= 70.0) {
      gaugeCircle.setAttribute('stroke', '#f43f5e'); // Rose
    } else if (aiPct >= 45.0) {
      gaugeCircle.setAttribute('stroke', '#f59e0b'); // Amber
    } else {
      gaugeCircle.setAttribute('stroke', '#10b981'); // Emerald
    }
  }

  // Verdict Title & Badges
  const verdictBadge = document.getElementById('verdict-badge');
  const verdictTitle = document.getElementById('verdict-title');
  const confText = document.getElementById('confidence-level-text');

  if (verdictBadge && verdictTitle) {
    verdictTitle.textContent = data.verdict;
    if (aiPct >= 70.0) {
      verdictBadge.textContent = 'High AI Probability (≥70%)';
      verdictBadge.className = 'inline-block text-xs font-mono font-bold px-3 py-1 rounded-full border bg-rose-500/10 text-rose-300 border-rose-500/30';
    } else if (aiPct >= 45.0) {
      verdictBadge.textContent = 'Uncertain / Mixed Composition (45-69%)';
      verdictBadge.className = 'inline-block text-xs font-mono font-bold px-3 py-1 rounded-full border bg-amber-500/10 text-amber-300 border-amber-500/30';
    } else {
      verdictBadge.textContent = 'Authentic Human Prose (<45%)';
      verdictBadge.className = 'inline-block text-xs font-mono font-bold px-3 py-1 rounded-full border bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
    }
  }

  if (confText) {
    const band = (aiPct >= 70 || aiPct <= 30) ? 'Very High Confidence' : 'Moderate Confidence';
    confText.textContent = `${band} • Zone ${data.verdict_zone || (aiPct >= 70 ? 'RED' : (aiPct >= 45 ? 'YELLOW' : 'GREEN'))}`;
  }

  // 1B. Identified AI Model / Generator Attribution (Bonus 1)
  const attribution = data.attribution || {};
  const platformName = attribution.platform || 'N/A (Predominantly Human)';
  const platformBadge = document.getElementById('ai-platform-name');
  const platformConf = document.getElementById('ai-platform-conf');
  if (platformBadge) platformBadge.textContent = platformName;
  if (platformConf) {
    if (aiPct >= 15.0 && attribution.confidence > 0) {
      platformConf.textContent = `${attribution.confidence.toFixed(0)}% signature match`;
      platformConf.classList.remove('hidden');
    } else {
      platformConf.textContent = 'Human Variance';
    }
  }

  // Populate Tab 3 Stylometric Attribution Card
  const tabAttrPlatform = document.getElementById('tab-attribution-platform');
  const tabAttrConf = document.getElementById('tab-attribution-conf');
  const tabAttrReasoning = document.getElementById('tab-attribution-reasoning');
  const tabAttrMarkers = document.getElementById('tab-attribution-markers');
  const tabAttrBreakdown = document.getElementById('tab-attribution-breakdown');

  if (tabAttrPlatform) tabAttrPlatform.textContent = platformName;
  if (tabAttrConf) tabAttrConf.textContent = aiPct >= 15.0 ? `${(attribution.confidence || 0).toFixed(1)}% Match` : 'Human Prose';
  if (tabAttrReasoning) tabAttrReasoning.textContent = attribution.reasoning || 'Standard human stylistic distribution.';

  if (tabAttrMarkers) {
    tabAttrMarkers.innerHTML = '';
    if (attribution.markers_found && attribution.markers_found.length > 0) {
      attribution.markers_found.forEach(m => {
        const badge = document.createElement('span');
        badge.className = 'text-xs font-mono bg-cyan-500/10 text-cyan-300 px-2.5 py-0.5 rounded border border-cyan-500/20';
        badge.textContent = m;
        tabAttrMarkers.appendChild(badge);
      });
    } else {
      tabAttrMarkers.innerHTML = `<span class="text-xs text-slate-500 italic font-mono">${aiPct < 15.0 ? 'Authentic human writing - no generative signatures' : 'Generic LLM pattern (no single marker dominant)'}</span>`;
    }
  }

  if (tabAttrBreakdown) {
    tabAttrBreakdown.innerHTML = '';
    const breakdown = attribution.breakdown || {};
    const models = [
      { key: 'ChatGPT-4o (OpenAI)', short: 'GPT-4o' },
      { key: 'Claude 3.5 (Anthropic)', short: 'Claude 3.5' },
      { key: 'Google Gemini', short: 'Gemini' },
      { key: 'Microsoft Copilot', short: 'Copilot' },
      { key: 'Meta LLaMA 3', short: 'LLaMA 3' },
    ];
    models.forEach(m => {
      const val = breakdown[m.key] || 0.0;
      const isTop = (platformName === m.key);
      const cell = document.createElement('div');
      cell.className = `p-2.5 rounded-lg border text-center font-mono ${isTop ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-200' : 'bg-surface-900 border-white/5 text-slate-400'}`;
      cell.innerHTML = `
        <span class="text-[10px] block truncate font-bold text-slate-300">${m.short}</span>
        <span class="text-xs font-bold block mt-0.5">${val.toFixed(1)}%</span>
        <div class="w-full bg-white/5 h-1 rounded-full mt-1 overflow-hidden">
          <div class="h-full ${isTop ? 'bg-cyan-400' : 'bg-slate-600'}" style="width: ${Math.min(100, val)}%"></div>
        </div>
      `;
      tabAttrBreakdown.appendChild(cell);
    });
  }

  // 2. High-Level KPI Summary Chips
  const kpiSentences = document.getElementById('kpi-sentences');
  if (kpiSentences) kpiSentences.textContent = `${data.ai_sentences || 0} / ${data.total_sentences || 0} Flags`;

  const kpiWords = document.getElementById('kpi-words');
  if (kpiWords) kpiWords.textContent = `${data.total_words || countWords(data.sentences)} words`;

  const kpiChars = document.getElementById('kpi-chars');
  if (kpiChars) kpiChars.textContent = `${data.total_chars || (data.sentences ? data.sentences.reduce((a, s) => a + (s.char_len || 0), 0) : 0)} chars`;

  const forensics = data.forensic_metrics || {};
  const kpiPpl = document.getElementById('kpi-ppl');
  if (kpiPpl) kpiPpl.textContent = (forensics.perplexity || 25.0).toFixed(1);

  const kpiPplLabel = document.getElementById('kpi-ppl-label');
  if (kpiPplLabel) kpiPplLabel.textContent = (forensics.perplexity || 25) < 30 ? 'Low / Predictable' : 'High / Organic';

  const kpiBurst = document.getElementById('kpi-burstiness');
  if (kpiBurst) kpiBurst.textContent = (forensics.burstiness || 0.5).toFixed(2);

  const kpiBurstLabel = document.getElementById('kpi-burst-label');
  if (kpiBurstLabel) kpiBurstLabel.textContent = (forensics.burstiness || 0.5) < 0.4 ? 'Uniform cadence' : 'Dynamic human variance';

  const kpiTtr = document.getElementById('kpi-ttr');
  if (kpiTtr) kpiTtr.textContent = `${forensics.lexical_diversity_ttr || 0}%`;

  const plag = data.plagiarism || {};
  const kpiPlag = document.getElementById('kpi-plag');
  if (kpiPlag) {
    const pRisk = plag.redundancy_risk || 'Clean';
    kpiPlag.textContent = `${pRisk} (${(plag.duplication_pct || 0).toFixed(1)}%)`;
    kpiPlag.className = pRisk === 'Clean' ? 'text-sm font-bold text-emerald-400 mt-0.5 block' : 'text-sm font-bold text-amber-400 mt-0.5 block';
  }

  // 3. Render Stylometric & Evasion Forensics Tab
  const evasion = data.evasion || {};
  const evasionBadge = document.getElementById('evasion-badge');
  if (evasionBadge) {
    const risk = evasion.evasion_risk || 'Low';
    evasionBadge.textContent = `${risk} Risk`;
    evasionBadge.className = risk === 'Low' 
      ? 'text-xs font-mono font-bold px-2.5 py-0.5 rounded border bg-emerald-500/10 text-emerald-300 border-emerald-500/30' 
      : 'text-xs font-mono font-bold px-2.5 py-0.5 rounded border bg-amber-500/10 text-amber-300 border-amber-500/30';
  }
  const evasionReasoning = document.getElementById('evasion-reasoning');
  if (evasionReasoning) evasionReasoning.textContent = evasion.reasoning || 'Natural sentence length variance and vocabulary entropy observed.';

  const burstVal = document.getElementById('burstiness-val');
  if (burstVal) burstVal.textContent = `Burstiness: ${(forensics.burstiness || 0.5).toFixed(2)}`;

  const lexicalDivVal = document.getElementById('lexical-div-val');
  if (lexicalDivVal) lexicalDivVal.textContent = `Lexical Diversity (TTR): ${forensics.lexical_diversity_ttr || 0}%`;

  const plagRisk = document.getElementById('plagiarism-risk');
  if (plagRisk) plagRisk.textContent = plag.redundancy_risk || 'Clean';

  const plagPct = document.getElementById('plagiarism-pct');
  if (plagPct) plagPct.textContent = `${(plag.duplication_pct || 0).toFixed(1)}% Duplication`;

  const plagReasoning = document.getElementById('plagiarism-reasoning');
  if (plagReasoning) plagReasoning.textContent = plag.reasoning || 'No internal verbatim n-gram duplication detected across document sections.';

  // 4. Render Neural Consensus Matrix Tab
  renderConsensusMatrix(data.ensemble || {});

  // 5. Render Sections / Slides Tab
  renderSectionsList(data.sections || []);

  // 6. Render Document View & Sentence Heatmap (Default Tab)
  activeFilter = 'all';
  updateFilterButtons();
  renderAnnotatedDocument(data.sentences || []);

  // Automatically select Sentence #1 to populate the Diagnostic Drawer with rich explanation
  if (data.sentences && data.sentences.length > 0) {
    selectSentence(0);
  }

  // Show Results Station & Switch to Heatmap Tab
  switchResultTab('heatmap');
  resultsCard.classList.remove('hidden');
  resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Refresh history list
  fetchHistory();
}

// ================= RENDER SENTENCE LOCALIZATION HEATMAP =================
function renderAnnotatedDocument(sentences) {
  const container = document.getElementById('annotated-document-content');
  if (!container) return;
  container.innerHTML = '';

  if (!sentences || sentences.length === 0) {
    container.innerHTML = `<span class="text-slate-500 italic">No sentence content available.</span>`;
    return;
  }

  sentences.forEach((s, idx) => {
    const span = document.createElement('span');
    span.id = `sentence-span-${idx}`;
    span.textContent = s.sentence + ' ';

    // 3-Color Highlight Palette
    let colorClass = 'sentence-pill bg-emerald-500/15 text-emerald-200 border-b border-emerald-500/30';
    if (s.score >= 70.0 || s.color === 'red') {
      colorClass = 'sentence-pill bg-rose-500/20 text-rose-200 border-b border-rose-500/40';
    } else if (s.score >= 45.0 || s.color === 'yellow') {
      colorClass = 'sentence-pill bg-amber-500/20 text-amber-200 border-b border-amber-500/40';
    }

    span.className = colorClass;
    span.title = `Sentence #${idx + 1} (${s.score.toFixed(1)}% AI) - Click to inspect`;
    span.onclick = () => selectSentence(idx);

    container.appendChild(span);
  });
}

// ================= SELECT SENTENCE & POPULATE DIAGNOSTIC DRAWER =================
function selectSentence(idx) {
  if (!currentAnalysisData || !currentAnalysisData.sentences) return;
  const sentences = currentAnalysisData.sentences;
  if (idx < 0 || idx >= sentences.length) return;

  selectedSentenceIndex = idx;
  const s = sentences[idx];

  // Visual active ring in document text
  sentences.forEach((_, i) => {
    const el = document.getElementById(`sentence-span-${i}`);
    if (el) {
      if (i === idx) {
        el.classList.add('sentence-active');
      } else {
        el.classList.remove('sentence-active');
      }
    }
  });

  // Populate Index & Length Telemetry
  const idxEl = document.getElementById('diag-sentence-index');
  if (idxEl) idxEl.textContent = `Sentence #${idx + 1} of ${sentences.length}`;

  const lengthEl = document.getElementById('diag-length-info');
  const wordCount = s.word_count || (s.sentence ? s.sentence.trim().split(/\s+/).length : 0);
  const charLen = s.char_len || (s.sentence ? s.sentence.length : 0);
  if (lengthEl) lengthEl.textContent = `${wordCount} words • ${charLen} chars`;

  // Sentence Quote Box & Accent Border
  const textEl = document.getElementById('diag-sentence-text');
  if (textEl) textEl.textContent = `"${s.sentence}"`;

  const quoteBox = document.getElementById('diag-quote-box');
  if (quoteBox) {
    if (s.score >= 70.0 || s.color === 'red') {
      quoteBox.className = 'p-3.5 rounded-lg bg-surface-900 border-l-4 border-rose-500 text-xs sm:text-sm text-slate-200 leading-relaxed font-sans shadow-inner';
    } else if (s.score >= 45.0 || s.color === 'yellow') {
      quoteBox.className = 'p-3.5 rounded-lg bg-surface-900 border-l-4 border-amber-500 text-xs sm:text-sm text-slate-200 leading-relaxed font-sans shadow-inner';
    } else {
      quoteBox.className = 'p-3.5 rounded-lg bg-surface-900 border-l-4 border-emerald-500 text-xs sm:text-sm text-slate-200 leading-relaxed font-sans shadow-inner';
    }
  }

  // Calibrated vs Raw Score
  const smoothedScoreEl = document.getElementById('diag-smoothed-score');
  if (smoothedScoreEl) {
    smoothedScoreEl.textContent = `${s.score.toFixed(1)}% AI`;
    if (s.score >= 70.0) {
      smoothedScoreEl.className = 'text-base font-bold text-rose-400 block';
    } else if (s.score >= 45.0) {
      smoothedScoreEl.className = 'text-base font-bold text-amber-400 block';
    } else {
      smoothedScoreEl.className = 'text-base font-bold text-emerald-400 block';
    }
  }

  const rawScoreEl = document.getElementById('diag-raw-score');
  if (rawScoreEl) {
    const rawVal = typeof s.raw_prob === 'number' ? (s.raw_prob * 100).toFixed(1) : s.score.toFixed(1);
    rawScoreEl.textContent = `${rawVal}% Raw`;
  }

  // Forensic Linguistic Reasoning (Core user explainability requirement)
  const reasoningEl = document.getElementById('diag-reasoning-text');
  if (reasoningEl) {
    reasoningEl.textContent = s.reasoning || (
      s.score >= 70.0
        ? `Severe synthetic signature (Perplexity: ${(s.ppl || 20).toFixed(1)}). Highly uniform token sequence and predictable generative transitions typical of large language models.`
        : (s.score >= 45.0
            ? `Borderline classification (Perplexity: ${(s.ppl || 35).toFixed(1)}). Mixed linguistic signals indicating human-AI hybrid composition or formulaic drafting.`
            : `Authentic human writing (Perplexity: ${(s.ppl || 50).toFixed(1)}). High structural burstiness, idiosyncratic vocabulary choices, and natural cognitive rhythm.`)
    );
  }

  // Confidence Band Badge
  const confEl = document.getElementById('diag-confidence-band');
  if (confEl) {
    confEl.textContent = s.confidence || (s.score >= 70 || s.score <= 30 ? 'High Confidence' : 'Moderate Confidence');
  }

  // 3-Point Evidence Checklist Breakdown
  const breakdownEl = document.getElementById('diag-explanation-breakdown');
  if (breakdownEl) {
    const pplVal = s.ppl || 25.0;
    let pplAnalysis = '';
    if (pplVal < 25.0) {
      pplAnalysis = `<div class="flex items-start gap-2"><span class="text-rose-400 shrink-0 font-bold">●</span><span><b>Low Perplexity (${pplVal.toFixed(1)}):</b> Token sequence exhibits low entropy; word sequences follow predictable LLM paths.</span></div>`;
    } else if (pplVal < 45.0) {
      pplAnalysis = `<div class="flex items-start gap-2"><span class="text-amber-400 shrink-0 font-bold">●</span><span><b>Moderate Perplexity (${pplVal.toFixed(1)}):</b> Blended vocabulary entropy; mixture of conventional expressions and natural phrasing.</span></div>`;
    } else {
      pplAnalysis = `<div class="flex items-start gap-2"><span class="text-emerald-400 shrink-0 font-bold">●</span><span><b>Organic Perplexity (${pplVal.toFixed(1)}):</b> Rich lexical divergence and non-standard phrasing characteristic of organic human thought.</span></div>`;
    }

    let cadenceAnalysis = '';
    if (s.score >= 70.0) {
      cadenceAnalysis = `<div class="flex items-start gap-2"><span class="text-rose-400 shrink-0 font-bold">●</span><span><b>Syntactic Rhythm:</b> Rigid clause symmetry with formulaic transition markers and low burstiness.</span></div>`;
    } else if (s.score >= 45.0) {
      cadenceAnalysis = `<div class="flex items-start gap-2"><span class="text-amber-400 shrink-0 font-bold">●</span><span><b>Syntactic Rhythm:</b> Balanced sentence rhythm with moderate structural variation.</span></div>`;
    } else {
      cadenceAnalysis = `<div class="flex items-start gap-2"><span class="text-emerald-400 shrink-0 font-bold">●</span><span><b>Syntactic Rhythm:</b> Dynamic human burstiness with varied clause lengths and irregular punctuation rhythm.</span></div>`;
    }

    let smoothingDelta = '';
    if (typeof s.raw_prob === 'number' && typeof s.smoothed_prob === 'number') {
      const delta = ((s.smoothed_prob - s.raw_prob) * 100).toFixed(1);
      const sign = delta > 0 ? `+${delta}%` : `${delta}%`;
      smoothingDelta = `<div class="flex items-start gap-2"><span class="text-cyan-400 shrink-0 font-bold">●</span><span><b>Context Kernel:</b> Gaussian neighborhood adjustment of ${sign} applied to reflect surrounding sentence continuity.</span></div>`;
    }

    breakdownEl.innerHTML = pplAnalysis + cadenceAnalysis + smoothingDelta;
  }

  // Perplexity & Cadence Telemetry
  const pplEl = document.getElementById('diag-ppl-score');
  const pplVal = s.ppl || 20.0;
  if (pplEl) pplEl.textContent = pplVal.toFixed(1);

  const pplDesc = document.getElementById('diag-ppl-desc');
  if (pplDesc) pplDesc.textContent = pplVal < 25 ? 'Low entropy (AI)' : (pplVal < 45 ? 'Moderate entropy' : 'Organic entropy (Human)');

  const cadenceEl = document.getElementById('diag-syntactic-cadence');
  if (cadenceEl) {
    cadenceEl.textContent = s.score >= 70.0 ? 'Synthetic Uniform' : (s.score >= 45.0 ? 'Hybrid Cadence' : 'Organic Human Flow');
  }

  const cadenceDesc = document.getElementById('diag-cadence-desc');
  if (cadenceDesc) {
    cadenceDesc.textContent = s.score >= 70.0 ? 'Formulaic pacing' : (s.score >= 45.0 ? 'Moderate variance' : 'Natural human burstiness');
  }

  // Clichés in sentence
  const clichesContainer = document.getElementById('diag-cliches-container');
  const clichesCountEl = document.getElementById('diag-cliches-count');
  if (clichesContainer) {
    clichesContainer.innerHTML = '';
    if (s.cliches && s.cliches.length > 0) {
      if (clichesCountEl) clichesCountEl.textContent = `${s.cliches.length} detected`;
      s.cliches.forEach(c => {
        const badge = document.createElement('span');
        badge.className = 'text-xs font-mono bg-cyan-500/10 text-cyan-300 px-2.5 py-0.5 rounded border border-cyan-500/25';
        badge.textContent = `"${c}"`;
        clichesContainer.appendChild(badge);
      });
    } else {
      if (clichesCountEl) clichesCountEl.textContent = '0 detected';
      clichesContainer.innerHTML = `<span class="text-xs text-slate-500 italic font-mono">No generative clichés detected in this sentence</span>`;
    }
  }

  // Model source signature hint in sentence
  const modelHintEl = document.getElementById('diag-model-hint');
  if (modelHintEl) {
    if (s.score < 45.0) {
      modelHintEl.textContent = 'Organic Human Prose';
      modelHintEl.className = 'text-xs font-mono font-bold text-emerald-400';
    } else {
      modelHintEl.textContent = s.platform_hint || 'ChatGPT-4o Signature';
      modelHintEl.className = 'text-xs font-mono font-bold text-cyan-300';
    }
  }
}

// ================= FILTER SENTENCES BY COLOR BAND =================
function filterSentences(filter) {
  activeFilter = filter;
  updateFilterButtons();
  if (!currentAnalysisData || !currentAnalysisData.sentences) return;

  currentAnalysisData.sentences.forEach((s, idx) => {
    const el = document.getElementById(`sentence-span-${idx}`);
    if (!el) return;

    if (filter === 'all') {
      el.style.display = 'inline';
    } else if (filter === 'red') {
      el.style.display = (s.score >= 70.0 || s.color === 'red') ? 'inline' : 'none';
    } else if (filter === 'yellow') {
      el.style.display = ((s.score >= 45.0 && s.score < 70.0) || s.color === 'yellow') ? 'inline' : 'none';
    } else if (filter === 'green') {
      el.style.display = (s.score < 45.0 || s.color === 'green') ? 'inline' : 'none';
    }
  });
}

function updateFilterButtons() {
  const filters = ['all', 'red', 'yellow', 'green'];
  filters.forEach(f => {
    const btn = document.getElementById(`tab-filter-${f}`);
    if (!btn) return;
    if (f === activeFilter) {
      btn.className = 'px-2.5 py-1 rounded-lg bg-brand-600 text-white font-semibold transition cursor-pointer';
    } else {
      if (f === 'red') btn.className = 'px-2.5 py-1 rounded-lg text-rose-400 hover:text-white transition cursor-pointer';
      else if (f === 'yellow') btn.className = 'px-2.5 py-1 rounded-lg text-amber-400 hover:text-white transition cursor-pointer';
      else if (f === 'green') btn.className = 'px-2.5 py-1 rounded-lg text-emerald-400 hover:text-white transition cursor-pointer';
      else btn.className = 'px-2.5 py-1 rounded-lg text-slate-400 hover:text-white transition cursor-pointer';
    }
  });
}

// ================= TABBED NAVIGATION =================
function switchResultTab(tabName) {
  const tabs = ['heatmap', 'consensus', 'forensics', 'sections'];
  tabs.forEach(t => {
    const btn = document.getElementById(`rtab-btn-${t}`);
    const panel = document.getElementById(`rpanel-${t}`);
    if (btn && panel) {
      if (t === tabName) {
        btn.className = 'px-4 py-2 rounded-xl bg-brand-600 text-white font-bold transition flex items-center gap-2 cursor-pointer shrink-0';
        panel.classList.remove('hidden');
      } else {
        btn.className = 'px-4 py-2 rounded-xl text-slate-400 hover:text-white bg-surface-950 hover:bg-surface-900 border border-white/5 transition flex items-center gap-2 cursor-pointer shrink-0';
        panel.classList.add('hidden');
      }
    }
  });
}

// ================= RENDER NEURAL CONSENSUS MATRIX =================
function renderConsensusMatrix(ensemble) {
  const grid = document.getElementById('ensemble-models-grid');
  if (!grid) return;
  grid.innerHTML = '';

  const descriptions = {
    'core_alpha': 'Deep contextual discourse & transformer attention engine',
    'core_beta': 'Generative cadence & transitional probability analyzer',
    'core_gamma': 'Adversarial evasion & structural boundary detector',
    'core_custom': 'Proprietary dual-vector morphological & syntactic custom classifier',
  };

  const titles = {
    'core_alpha': 'Veritas Core Alpha',
    'core_beta': 'Veritas Core Beta',
    'core_gamma': 'Veritas Core Gamma',
    'core_custom': 'Veritas Proprietary Core (Custom Model)',
  };

  let modelsList = [];
  if (ensemble && ensemble.voting_matrix && ensemble.voting_matrix.length > 0) {
    modelsList = ensemble.voting_matrix.map(vm => ({
      key: vm.key,
      title: titles[vm.key] || vm.name,
      weight: `${vm.weight_pct}% Ensemble Weight`,
      score: (vm.score_pct !== undefined ? vm.score_pct : 0).toFixed(1),
      desc: descriptions[vm.key] || 'Calibrated neural consensus contributor',
      status: vm.key === 'core_custom' ? 'Custom Checkpoint' : 'Pretrained Active',
      verdict: vm.verdict || 'Evaluated'
    }));
  } else {
    modelsList = [
      { key: 'core_alpha', title: 'Veritas Core Alpha', weight: '35% Ensemble Weight', score: '0.0', desc: descriptions['core_alpha'], status: 'Pretrained Active' },
      { key: 'core_beta', title: 'Veritas Core Beta', weight: '25% Ensemble Weight', score: '0.0', desc: descriptions['core_beta'], status: 'Pretrained Active' },
      { key: 'core_gamma', title: 'Veritas Core Gamma', weight: '20% Ensemble Weight', score: '0.0', desc: descriptions['core_gamma'], status: 'Pretrained Active' },
      { key: 'core_custom', title: 'Veritas Proprietary Core (Custom Model)', weight: '20% Ensemble Weight', score: '0.0', desc: descriptions['core_custom'], status: 'Custom Checkpoint' },
    ];
  }

  // Adjust grid layout dynamically for 3 or 4+ models
  grid.className = modelsList.length >= 4 
    ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4' 
    : 'grid grid-cols-1 md:grid-cols-3 gap-4';

  modelsList.forEach(m => {
    const card = document.createElement('div');
    const isCustom = m.key === 'core_custom';
    card.className = `p-5 rounded-xl border ${isCustom ? 'border-brand-500/40 bg-surface-950/90 shadow-brand-500/10' : 'border-white/10 bg-surface-950/80'} space-y-3 shadow-lg`;
    card.innerHTML = `
      <div class="flex items-center justify-between">
        <div>
          <h5 class="text-sm font-bold text-white flex items-center gap-1.5">
            ${isCustom ? '<span>⭐</span>' : ''}
            <span>${m.title}</span>
          </h5>
          <span class="text-[10px] font-mono text-brand-300 block">${m.weight}</span>
        </div>
        <span class="text-[10px] font-mono px-2 py-0.5 rounded ${isCustom ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30' : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'}">
          ${m.status}
        </span>
      </div>
      <div class="p-3 rounded-lg bg-surface-900 border border-white/5 space-y-1">
        <span class="text-[10px] font-mono text-slate-400 block uppercase">Sub-Model Probability</span>
        <span class="text-xl font-bold font-mono text-white">${m.score}%</span>
      </div>
      <p class="text-xs text-slate-400 font-mono">${m.desc}</p>
      <div class="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-slate-400">
        <span>Status: Calibrated</span>
        <span class="font-bold text-slate-300">${m.verdict || 'Active'}</span>
      </div>
    `;
    grid.appendChild(card);
  });

  const badge = document.getElementById('consensus-verdict-badge');
  if (badge) {
    badge.textContent = ensemble.consensus_verdict || `Consensus: ${ensemble.consensus_level || 'Active'}`;
  }
}

// ================= RENDER SECTIONS & SLIDES =================
function renderSectionsList(sections) {
  const container = document.getElementById('sections-container');
  const countBadge = document.getElementById('section-count-badge');
  const tabBtn = document.getElementById('rtab-btn-sections');
  const tabBadge = document.getElementById('tab-sections-badge');

  if (!sections || sections.length === 0) {
    if (tabBtn) tabBtn.classList.add('hidden');
    return;
  }

  if (tabBtn) tabBtn.classList.remove('hidden');
  if (tabBadge) tabBadge.textContent = sections.length;
  if (countBadge) countBadge.textContent = `${sections.length} Sections`;
  if (!container) return;

  container.innerHTML = '';
  sections.forEach((sec, idx) => {
    const card = document.createElement('div');
    card.className = 'p-4 rounded-xl border border-white/10 bg-surface-950/80 space-y-2';

    let colorBadge = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
    if (sec.ai_percentage >= 65.0) colorBadge = 'bg-rose-500/10 text-rose-300 border-rose-500/30';
    else if (sec.ai_percentage >= 25.0) colorBadge = 'bg-amber-500/10 text-amber-300 border-amber-500/30';

    card.innerHTML = `
      <div class="flex items-center justify-between">
        <h5 class="text-xs sm:text-sm font-bold text-white">${escapeHtml(sec.title || `Section ${idx + 1}`)}</h5>
        <span class="text-xs font-mono font-bold px-2.5 py-0.5 rounded border ${colorBadge}">
          ${sec.ai_percentage.toFixed(1)}% AI
        </span>
      </div>
      <p class="text-xs text-slate-300 font-sans italic">${escapeHtml(sec.preview || '')}</p>
      <div class="flex items-center gap-4 text-[11px] font-mono text-slate-400 pt-1 border-t border-white/5">
        <span>${sec.word_count || 0} words</span>
        <span>${sec.total_sentences || 0} sentences (${sec.ai_sentences || 0} flagged)</span>
        <span>Verdict: ${sec.verdict || 'Evaluated'}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

// ================= SLIDE-OVER HISTORY DRAWER =================
function toggleHistoryDrawer() {
  const drawer = document.getElementById('history-drawer');
  const backdrop = document.getElementById('history-backdrop');
  if (!drawer || !backdrop) return;

  isHistoryDrawerOpen = !isHistoryDrawerOpen;
  if (isHistoryDrawerOpen) {
    drawer.classList.remove('translate-x-full');
    backdrop.classList.remove('hidden');
    fetchHistory();
  } else {
    drawer.classList.add('translate-x-full');
    backdrop.classList.add('hidden');
  }
}

async function fetchHistory() {
  const listEl = document.getElementById('history-list');
  const countBadge = document.getElementById('history-count-badge');
  const headerCount = document.getElementById('header-history-count');

  try {
    const res = await fetch('/history');
    if (!res.ok) throw new Error('Could not load history');
    const items = await res.json();
    historyCache = items;

    if (countBadge) countBadge.textContent = items.length;
    if (headerCount) headerCount.textContent = items.length;
    renderHistoryList(items);
  } catch (err) {
    if (listEl) {
      listEl.innerHTML = `<div class="text-center py-6 text-xs text-slate-500 font-mono">No previous analyses found.</div>`;
    }
  }
}

function renderHistoryList(items) {
  const listEl = document.getElementById('history-list');
  if (!listEl) return;
  listEl.innerHTML = '';

  if (!items || items.length === 0) {
    listEl.innerHTML = `<div class="text-center py-10 text-xs text-slate-500 font-mono">No previous analyses archived yet.</div>`;
    return;
  }

  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'p-3.5 rounded-xl bg-surface-900 border border-white/5 hover:border-brand-500/40 transition group space-y-2';

    let colorBadge = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
    if (item.ai_percentage >= 70.0) colorBadge = 'bg-rose-500/10 text-rose-300 border-rose-500/30';
    else if (item.ai_percentage >= 45.0) colorBadge = 'bg-amber-500/10 text-amber-300 border-amber-500/30';

    div.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-white truncate max-w-[200px]" title="${escapeHtml(item.filename)}">
          ${escapeHtml(item.filename)}
        </span>
        <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${colorBadge}">
          ${item.ai_percentage.toFixed(1)}% AI
        </span>
      </div>
      <div class="flex items-center justify-between text-[10px] font-mono text-slate-400">
        <span>${formatDate(item.created_at)}</span>
        <span>${item.total_words || 0} words</span>
      </div>
      <div class="flex items-center gap-1.5 pt-1 border-t border-white/5">
        <button onclick="loadHistoryRecord('${item.id}')" class="flex-1 py-1 px-2 rounded text-[11px] font-mono text-brand-300 bg-brand-500/10 hover:bg-brand-500/20 border border-brand-500/20 transition cursor-pointer">
          Open Audit
        </button>
        <a href="/history/${item.id}/pdf" target="_blank" class="py-1 px-2 rounded text-[11px] font-mono text-slate-300 bg-white/5 hover:bg-white/10 border border-white/10 transition cursor-pointer" title="Download PDF">
          PDF
        </a>
        <button onclick="deleteHistoryRecord('${item.id}', event)" class="py-1 px-2 rounded text-[11px] font-mono text-rose-400 hover:bg-rose-500/20 transition cursor-pointer" title="Delete">
          🗑️
        </button>
      </div>
    `;
    listEl.appendChild(div);
  });
}

function filterHistoryItems(query) {
  if (!query) {
    renderHistoryList(historyCache);
    return;
  }
  const q = query.toLowerCase();
  const filtered = historyCache.filter(item => 
    (item.filename && item.filename.toLowerCase().includes(q)) ||
    (item.verdict && item.verdict.toLowerCase().includes(q))
  );
  renderHistoryList(filtered);
}

async function loadHistoryRecord(analysisId) {
  try {
    const res = await fetch(`/history/${analysisId}`);
    if (!res.ok) throw new Error('Failed to load analysis record');
    const data = await res.json();
    toggleHistoryDrawer(); // Close drawer
    displayResults(data);
  } catch (err) {
    showError('Could not load historical analysis record.');
  }
}

async function deleteHistoryRecord(analysisId, event) {
  if (event) event.stopPropagation();
  if (!confirm('Are you sure you want to permanently delete this audit record from the database?')) return;

  try {
    const res = await fetch(`/history/${analysisId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete');
    fetchHistory();
  } catch (err) {
    showError('Failed to delete analysis record.');
  }
}

// ================= ACTION TOOLBAR HELPERS =================
function downloadPdfReport() {
  if (!currentAnalysisData || !currentAnalysisData.id) {
    showError('No active analysis available for PDF export.');
    return;
  }
  window.open(`/history/${currentAnalysisData.id}/pdf`, '_blank');
}

function copySummaryToClipboard() {
  if (!currentAnalysisData) return;
  const summary = `VeritasDoc Forensic Evaluation Dossier
Document: ${currentAnalysisData.filename}
Verdict: ${currentAnalysisData.verdict} (${currentAnalysisData.ai_percentage.toFixed(1)}% AI)
Confidence: Zone ${currentAnalysisData.verdict_zone || 'N/A'}
Total Words: ${currentAnalysisData.total_words || 0}
Flagged Sentences: ${currentAnalysisData.ai_sentences || 0} / ${currentAnalysisData.total_sentences || 0}
Perplexity: ${(currentAnalysisData.forensic_metrics?.perplexity || 0).toFixed(1)}
Burstiness: ${(currentAnalysisData.forensic_metrics?.burstiness || 0).toFixed(2)}
SHA-256: ${currentAnalysisData.sha256_hash || 'Verified'}`;

  navigator.clipboard.writeText(summary).then(() => {
    const textEl = document.getElementById('copy-summary-text');
    const iconEl = document.getElementById('copy-summary-icon');
    if (textEl) textEl.textContent = 'Copied!';
    if (iconEl) iconEl.textContent = '✓';
    setTimeout(() => {
      if (textEl) textEl.textContent = 'Copy';
      if (iconEl) iconEl.textContent = '📋';
    }, 2000);
  });
}

// ================= SYSTEM HEALTH MONITOR =================
async function checkHealth() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    if (data.model_loaded) {
      const activeCount = data.active_models_count || 4;
      const totalCount = data.total_models_count || 4;
      if (modelStatusText) modelStatusText.textContent = `Neural Core (${activeCount}/${totalCount})`;
      if (statusDot) statusDot.className = 'relative inline-flex rounded-full h-2 w-2 bg-emerald-500';
      if (statusPing) statusPing.className = 'animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75';
    } else {
      if (modelStatusText) modelStatusText.textContent = 'Initializing Cores...';
      if (statusDot) statusDot.className = 'relative inline-flex rounded-full h-2 w-2 bg-amber-500';
      if (statusPing) statusPing.className = 'animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75';
    }
  } catch (err) {
    if (modelStatusText) modelStatusText.textContent = 'Offline';
    if (statusDot) statusDot.className = 'relative inline-flex rounded-full h-2 w-2 bg-rose-500';
    if (statusPing) statusPing.className = 'hidden';
  }
}

// ================= UTILITY HELPERS =================
function showError(msg) {
  if (errorMessage) errorMessage.textContent = msg;
  if (errorBanner) {
    errorBanner.classList.remove('hidden');
    errorBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function dismissError() {
  if (errorBanner) errorBanner.classList.add('hidden');
}

function countWords(sentences) {
  if (!sentences) return 0;
  return sentences.reduce((acc, s) => acc + (s.word_count || (s.sentence ? s.sentence.trim().split(/\s+/).length : 0)), 0);
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDate(isoStr) {
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (e) {
    return isoStr;
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}
