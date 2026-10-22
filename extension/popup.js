document.getElementById("inspect-btn").addEventListener("click", async () => {
  const text = document.getElementById("inspect-text").value.trim();
  const resBox = document.getElementById("result-box");
  const verdictEl = document.getElementById("res-verdict");
  const scoreEl = document.getElementById("res-score");
  const detailsEl = document.getElementById("res-details");

  if (!text) return;

  resBox.style.display = "block";
  verdictEl.textContent = "Scanning...";
  scoreEl.textContent = "";
  detailsEl.textContent = "Connecting to VeritasDoc neural consensus...";

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
    verdictEl.textContent = data.verdict;
    verdictEl.style.color = color;
    scoreEl.textContent = `${data.ai_percentage}% AI`;
    scoreEl.style.color = color;
    detailsEl.innerHTML = `
      Platform: <b>${data.attribution?.platform || 'N/A'}</b><br>
      Perplexity: ${data.forensic_metrics?.perplexity || 0} &bull; Burstiness: ${data.forensic_metrics?.burstiness || 0}<br>
      Evasion: ${data.evasion?.humanizer_risk || 'Low'} Risk &bull; ${data.total_words} words evaluated
    `;
  } catch (err) {
    verdictEl.textContent = "Offline";
    verdictEl.style.color = "#f43f5e";
    detailsEl.textContent = "Ensure local server is running on http://localhost:8000";
  }
});
