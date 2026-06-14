const apiStatus = document.querySelector("#api-status");
const assetForm = document.querySelector("#asset-form");
const detectionForm = document.querySelector("#detection-form");
const assetList = document.querySelector("#asset-list");
const detectionResult = document.querySelector("#detection-result");
const detectionHistory = document.querySelector("#detection-history");
const reviewList = document.querySelector("#review-list");

document.querySelector("#refresh-assets").addEventListener("click", loadAssets);
document.querySelector("#refresh-detections").addEventListener("click", loadDetections);
document.querySelector("#refresh-review").addEventListener("click", loadReviewCases);
assetForm.addEventListener("submit", registerAsset);
detectionForm.addEventListener("submit", runDetection);

function setMessage(id, text, isError = false) {
  const element = document.querySelector(id);
  element.textContent = text;
  element.classList.toggle("error", isError);
}

function formatScore(value) {
  if (value === undefined || value === null) {
    return "n/a";
  }
  return Number(value).toFixed(3);
}

function actionClass(action, score) {
  if (action === "high_confidence_match" || score >= 0.9) {
    return "high";
  }
  if (action === "human_review" || score >= 0.7) {
    return "review";
  }
  return "none";
}

function actionLabel(action) {
  const labels = {
    high_confidence_match: "High confidence",
    human_review: "Human review",
    no_action: "No action",
  };
  return labels[action] || action || "No match";
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof payload === "object" ? payload.detail : payload;
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return payload;
}

async function checkApi() {
  try {
    await requestJson("/healthz");
    apiStatus.textContent = "API online";
    apiStatus.className = "status-pill ok";
  } catch (error) {
    apiStatus.textContent = "API offline";
    apiStatus.className = "status-pill error";
  }
}

function ensureWav(file) {
  if (!file || !file.name.toLowerCase().endsWith(".wav")) {
    throw new Error("Please choose a .wav file.");
  }
}

async function registerAsset(event) {
  event.preventDefault();
  setMessage("#asset-message", "Registering asset...");
  const button = document.querySelector("#asset-submit");
  button.disabled = true;

  try {
    const file = document.querySelector("#asset-file").files[0];
    ensureWav(file);
    const formData = new FormData(assetForm);
    const asset = await requestJson("/v1/assets", {
      method: "POST",
      body: formData,
    });
    assetForm.reset();
    setMessage("#asset-message", `Registered ${asset.asset_id}.`);
    await loadAssets();
  } catch (error) {
    setMessage("#asset-message", error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function runDetection(event) {
  event.preventDefault();
  setMessage("#detection-message", "Running detection...");
  const button = document.querySelector("#detection-submit");
  button.disabled = true;

  try {
    const file = document.querySelector("#detection-file").files[0];
    ensureWav(file);
    const formData = new FormData(detectionForm);
    const detection = await requestJson("/v1/detections", {
      method: "POST",
      body: formData,
    });
    detectionForm.reset();
    setMessage("#detection-message", `Detection ${detection.detection_id} completed.`);
    renderDetectionResult(detection);
    await Promise.all([loadDetections(), loadReviewCases()]);
  } catch (error) {
    setMessage("#detection-message", error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function loadAssets() {
  try {
    const assets = await requestJson("/v1/assets");
    if (!assets.length) {
      assetList.className = "list empty";
      assetList.textContent = "No assets registered yet.";
      return;
    }

    assetList.className = "list";
    assetList.innerHTML = assets
      .map(
        (asset) => `
          <article class="item">
            <div class="item-header">
              <div class="item-title">${escapeHtml(asset.title)}</div>
              <span class="badge none">${escapeHtml(asset.asset_id)}</span>
            </div>
            <div class="meta">Owner: ${escapeHtml(asset.owner)} · Duration: ${formatScore(asset.duration_seconds)}s</div>
            <div class="meta">File: ${escapeHtml(asset.metadata?.source_filename || "n/a")}</div>
          </article>
        `,
      )
      .join("");
  } catch (error) {
    assetList.className = "list empty";
    assetList.textContent = error.message;
  }
}

async function loadDetections() {
  try {
    const detections = await requestJson("/v1/detections");
    if (!detections.length) {
      detectionHistory.className = "list empty";
      detectionHistory.textContent = "No detection history yet.";
      return;
    }

    detectionHistory.className = "list";
    detectionHistory.innerHTML = detections
      .slice()
      .reverse()
      .map(renderDetectionCard)
      .join("");
  } catch (error) {
    detectionHistory.className = "list empty";
    detectionHistory.textContent = error.message;
  }
}

function renderDetectionResult(detection) {
  detectionResult.className = "result";
  detectionResult.innerHTML = renderDetectionCard(detection);
}

function renderDetectionCard(detection) {
  const bestMatch = detection.matches?.[0];
  if (!bestMatch) {
    return `
      <article class="item">
        <div class="item-header">
          <div class="item-title">${escapeHtml(detection.detection_id)}</div>
          <span class="badge none">No action</span>
        </div>
        <div class="meta">No candidate matched this query.</div>
      </article>
    `;
  }

  const badgeClass = actionClass(bestMatch.action, bestMatch.final_score);
  return `
    <article class="item">
      <div class="item-header">
        <div>
          <div class="item-title">${escapeHtml(bestMatch.metadata?.reference?.title || bestMatch.asset_id)}</div>
          <div class="meta">Detection: ${escapeHtml(detection.detection_id)} · Asset: ${escapeHtml(bestMatch.asset_id)}</div>
        </div>
        <span class="badge ${badgeClass}">${actionLabel(bestMatch.action)}</span>
      </div>
      <div class="score-grid">
        <div class="score-box"><span>Final</span>${formatScore(bestMatch.final_score)}</div>
        <div class="score-box"><span>Fingerprint</span>${formatScore(bestMatch.fingerprint_score)}</div>
        <div class="score-box"><span>Embedding</span>${formatScore(bestMatch.embedding_score)}</div>
        <div class="score-box"><span>Alignment</span>${formatScore(bestMatch.alignment_score)}</div>
      </div>
    </article>
  `;
}

async function loadReviewCases() {
  try {
    const cases = await requestJson("/v1/review-cases");
    if (!cases.length) {
      reviewList.className = "list empty";
      reviewList.textContent = "No open review cases.";
      return;
    }

    reviewList.className = "list";
    reviewList.innerHTML = cases.map(renderReviewCase).join("");
    reviewList.querySelectorAll("[data-review-action]").forEach((button) => {
      button.addEventListener("click", submitReviewDecision);
    });
  } catch (error) {
    reviewList.className = "list empty";
    reviewList.textContent = error.message;
  }
}

function renderReviewCase(reviewCase) {
  const match = reviewCase.match || {};
  return `
    <article class="item" data-detection-id="${escapeHtml(reviewCase.detection_id)}">
      <div class="item-header">
        <div>
          <div class="item-title">${escapeHtml(match.metadata?.reference?.title || match.asset_id || "Review case")}</div>
          <div class="meta">Detection: ${escapeHtml(reviewCase.detection_id)} · Score: ${formatScore(match.final_score)}</div>
        </div>
        <span class="badge review">Human review</span>
      </div>
      <div class="review-actions">
        <input data-reviewer placeholder="Reviewer" value="local-tester" />
        <input data-notes placeholder="Notes" />
        <button data-review-action="approve" type="button">Approve</button>
        <button data-review-action="reject" type="button">Reject</button>
        <button data-review-action="escalate" type="button">Escalate</button>
      </div>
    </article>
  `;
}

async function submitReviewDecision(event) {
  const button = event.currentTarget;
  const item = button.closest("[data-detection-id]");
  const detectionId = item.dataset.detectionId;
  const reviewer = item.querySelector("[data-reviewer]").value.trim();
  const notes = item.querySelector("[data-notes]").value.trim();
  const decision = button.dataset.reviewAction;

  setMessage("#review-message", `Saving ${decision} for ${detectionId}...`);
  try {
    await requestJson(`/v1/review-cases/${encodeURIComponent(detectionId)}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, reviewer, notes }),
    });
    setMessage("#review-message", `Review case ${detectionId} closed.`);
    await loadReviewCases();
  } catch (error) {
    setMessage("#review-message", error.message, true);
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

checkApi();
loadAssets();
loadDetections();
loadReviewCases();

