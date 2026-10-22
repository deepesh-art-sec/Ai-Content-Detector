/**
 * VeritasDoc Manifest V3 Content Script
 * Injects a floating inspector badge on selected text in Canvas, Moodle, or any web document.
 */

let floatingPill = null;

document.addEventListener("mouseup", (e) => {
  const selection = window.getSelection().toString().trim();
  if (selection.length > 80) {
    showVeritasPill(e.pageX, e.pageY, selection);
  } else {
    removeVeritasPill();
  }
});

function removeVeritasPill() {
  if (floatingPill && floatingPill.parentNode) {
    floatingPill.parentNode.removeChild(floatingPill);
    floatingPill = null;
  }
}

function showVeritasPill(x, y, text) {
  removeVeritasPill();

  floatingPill = document.createElement("div");
  floatingPill.id = "veritasdoc-floating-inspector";
  floatingPill.style.position = "absolute";
  floatingPill.style.left = `${x + 10}px`;
  floatingPill.style.top = `${y + 10}px`;
  floatingPill.style.zIndex = "999999";
  floatingPill.style.background = "#0f172a";
  floatingPill.style.color = "#ffffff";
  floatingPill.style.padding = "8px 14px";
  floatingPill.style.borderRadius = "10px";
  floatingPill.style.boxShadow = "0 10px 25px rgba(0,0,0,0.5)";
  floatingPill.style.fontFamily = "system-ui, -apple-system, sans-serif";
  floatingPill.style.fontSize = "12px";
  floatingPill.style.cursor = "pointer";
  floatingPill.style.border = "1px solid #4f46e5";
  floatingPill.innerHTML = `
    <div style="display:flex; align-items:center; gap:8px;">
      <span style="background:#4f46e5; border-radius:4px; padding:2px 5px; font-weight:bold; font-size:10px;">Ψ VeritasDoc</span>
      <span>Inspect with Multi-Vector AI Core...</span>
    </div>
  `;

  floatingPill.addEventListener("click", async () => {
    floatingPill.innerHTML = `<span>Scanning neural consensus...</span>`;
    try {
      const res = await fetch("http://localhost:8000/recalculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          sensitivity: "balanced",
          esl_safeguard: true
        })
      });
      const data = await res.json();
      const color = data.verdict_zone === "RED" ? "#f43f5e" : (data.verdict_zone === "YELLOW" ? "#f59e0b" : "#10b981");
      floatingPill.innerHTML = `
        <div style="max-width:280px; text-align:left;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span style="font-weight:bold; color:${color};">${data.verdict}</span>
            <span style="font-weight:bold; font-size:13px; color:${color};">${data.ai_percentage}% AI</span>
          </div>
          <div style="font-size:10px; color:#94a3b8; line-height:1.3;">
            Platform: ${data.attribution?.platform || 'N/A'}<br>
            PPL: ${data.forensic_metrics?.perplexity || 0} &bull; Burstiness: ${data.forensic_metrics?.burstiness || 0}
          </div>
        </div>
      `;
    } catch (err) {
      floatingPill.innerHTML = `<span style="color:#f43f5e;">Local server offline (http://localhost:8000)</span>`;
    }
  });

  document.body.appendChild(floatingPill);
}
