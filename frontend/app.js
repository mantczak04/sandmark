const API_BASE = "http://localhost:8000";

const mrUrlInput = document.getElementById("mr-url");
const promptSelect = document.getElementById("prompt-select");
const promptTabSelect = document.getElementById("prompt-tab-select");
const promptTabCustom = document.getElementById("prompt-tab-custom");
const promptPanelSelect = document.getElementById("prompt-panel-select");
const promptPanelCustom = document.getElementById("prompt-panel-custom");
const customPromptNameInput = document.getElementById("custom-prompt-name");
const customPromptContentInput = document.getElementById("custom-prompt-content");
const btnSavePrompt = document.getElementById("btn-save-prompt");
const btnFetchDiff = document.getElementById("btn-fetch-diff");
const btnRunReview = document.getElementById("btn-run-review");
const errorBanner = document.getElementById("error-banner");
const loadingEl = document.getElementById("loading");
const statsSection = document.getElementById("stats-section");
const statTokens = document.getElementById("stat-tokens");
const statTime = document.getElementById("stat-time");
const statComments = document.getElementById("stat-comments");
const summarySection = document.getElementById("summary-section");
const reviewSummary = document.getElementById("review-summary");
const diffSection = document.getElementById("diff-section");
const diffContainer = document.getElementById("diff-container");
const logsBody = document.getElementById("logs-body");
const btnCopyCsv = document.getElementById("btn-copy-csv");
const btnDownloadCsv = document.getElementById("btn-download-csv");

let currentDiffData = null;

// --- Utilities ---
function showError(msg) {
    errorBanner.textContent = msg;
    errorBanner.hidden = false;
    console.error(msg);
}

function clearError() {
    errorBanner.hidden = true;
    errorBanner.textContent = "";
}

function setLoading(on) {
    loadingEl.hidden = !on;
    btnFetchDiff.disabled = on;
    btnRunReview.disabled = on;
    btnSavePrompt.disabled = on;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// --- Fetch helper ---
function fetchWithTimeout(url, options = {}) {
    return fetch(url, options);
}

// --- Load prompts ---
function setActivePromptTab(tab) {
    const selectActive = tab === "select";
    promptTabSelect.classList.toggle("active", selectActive);
    promptTabCustom.classList.toggle("active", !selectActive);
    promptPanelSelect.hidden = !selectActive;
    promptPanelCustom.hidden = selectActive;
}

async function loadPrompts(selectedPrompt = null) {
    console.log("Loading prompts from backend...");
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/prompts`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        promptSelect.innerHTML = "";
        if (data.prompts.length === 0) {
            promptSelect.innerHTML = '<option value="">No prompts found</option>';
            return;
        }
        for (const p of data.prompts) {
            const opt = document.createElement("option");
            opt.value = p;
            opt.textContent = p;
            promptSelect.appendChild(opt);
        }
        if (selectedPrompt && data.prompts.includes(selectedPrompt)) {
            promptSelect.value = selectedPrompt;
        }
        console.log(`Loaded ${data.prompts.length} prompts`);
    } catch (e) {
        console.error("Failed to load prompts:", e.message);
        promptSelect.innerHTML = '<option value="">Error loading prompts</option>';
        showError("Failed to load prompts: " + e.message);
    }
}

// --- Fetch diff ---
btnFetchDiff.addEventListener("click", async () => {
    clearError();
    const mrUrl = mrUrlInput.value.trim();
    if (!mrUrl) {
        showError("Please enter a GitLab MR URL.");
        return;
    }

    setLoading(true);
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/diff`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mr_url: mrUrl }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to fetch diff");
        }
        currentDiffData = await res.json();
        renderDiff(currentDiffData, []);
        diffSection.hidden = false;
        btnRunReview.disabled = false;
    } catch (e) {
        showError(e.message);
    } finally {
        setLoading(false);
    }

});

// --- Run review ---
btnRunReview.addEventListener("click", async () => {
    clearError();
    const mrUrl = mrUrlInput.value.trim();
    const promptName = promptSelect.value;
    if (!mrUrl) {
        showError("Please enter a GitLab MR URL.");
        return;
    }
    if (!promptName) {
        showError("Please select a master prompt.");
        return;
    }

    setLoading(true);
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/review`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mr_url: mrUrl, prompt_name: promptName }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Review failed");
        }
        const result = await res.json();

        // Show stats
        statTokens.textContent = result.tokens_used.toLocaleString();
        statTime.textContent = result.time_seconds + "s";
        statComments.textContent = result.review.comments.length;
        statsSection.hidden = false;

        // Show summary
        reviewSummary.textContent = result.review.summary;
        summarySection.hidden = false;

        // Re-render diff with comments
        if (currentDiffData) {
            renderDiff(currentDiffData, result.review.comments);
        }
        diffSection.hidden = false;

        // Refresh logs
        await loadLogs();
    } catch (e) {
        showError(e.message);
    } finally {
        setLoading(false);
    }

});

promptTabSelect.addEventListener("click", () => setActivePromptTab("select"));
promptTabCustom.addEventListener("click", () => setActivePromptTab("custom"));

btnSavePrompt.addEventListener("click", async () => {
    clearError();
    const promptName = customPromptNameInput.value.trim();
    const promptContent = customPromptContentInput.value.trim();

    if (!promptName) {
        showError("Please enter a prompt filename.");
        return;
    }
    if (!promptContent) {
        showError("Please enter prompt content.");
        return;
    }

    setLoading(true);
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/prompts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt_name: promptName, content: promptContent }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to save prompt");
        }
        const data = await res.json();
        await loadPrompts(data.prompt_name);
        setActivePromptTab("select");
    } catch (e) {
        showError(e.message);
    } finally {
        setLoading(false);
    }
});

// --- Render Diff ---
function parseDiffLines(diffText) {
    const lines = diffText.split("\n");
    const parsed = [];
    let newLineNum = 0;

    for (const line of lines) {
        const hunkMatch = line.match(/^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
        if (hunkMatch) {
            newLineNum = parseInt(hunkMatch[1], 10);
            parsed.push({ type: "hunk", text: line, lineNum: null });
            continue;
        }

        if (line.startsWith("+")) {
            parsed.push({ type: "add", text: line.substring(1), lineNum: newLineNum });
            newLineNum++;
        } else if (line.startsWith("-")) {
            parsed.push({ type: "del", text: line.substring(1), lineNum: null });
        } else {
            parsed.push({ type: "context", text: line.substring(1) || line, lineNum: newLineNum });
            newLineNum++;
        }
    }
    return parsed;
}

function renderDiff(diffData, comments) {
    diffContainer.innerHTML = "";

    // Group comments by file and line
    const commentMap = {};
    for (const c of comments) {
        const key = `${c.file}:${c.line}`;
        if (!commentMap[key]) commentMap[key] = [];
        commentMap[key].push(c);
    }

    for (const file of diffData.files) {
        const fileEl = document.createElement("div");
        fileEl.className = "diff-file";

        // Header
        const headerEl = document.createElement("div");
        headerEl.className = "diff-file-header";
        let label = file.new_path;
        if (file.new_file) label += " (new)";
        if (file.deleted_file) label += " (deleted)";
        if (file.renamed_file) label += ` (renamed from ${file.old_path})`;
        headerEl.textContent = label;
        fileEl.appendChild(headerEl);

        // Diff table
        const table = document.createElement("table");
        table.className = "diff-table";
        const tbody = document.createElement("tbody");

        const lines = parseDiffLines(file.diff);
        for (const line of lines) {
            const tr = document.createElement("tr");

            if (line.type === "hunk") {
                tr.className = "diff-line-hunk";
                const td = document.createElement("td");
                td.colSpan = 2;
                td.textContent = line.text;
                tr.appendChild(td);
            } else {
                const cls =
                    line.type === "add" ? "diff-line-add" :
                    line.type === "del" ? "diff-line-del" : "";
                if (cls) tr.className = cls;

                const numTd = document.createElement("td");
                numTd.className = "diff-line-num";
                numTd.textContent = line.lineNum ?? "";
                tr.appendChild(numTd);

                const codeTd = document.createElement("td");
                const prefix = line.type === "add" ? "+" : line.type === "del" ? "-" : " ";
                codeTd.textContent = prefix + line.text;
                tr.appendChild(codeTd);
            }
            tbody.appendChild(tr);

            // Insert review comments after this line
            if (line.lineNum !== null) {
                const key = `${file.new_path}:${line.lineNum}`;
                if (commentMap[key]) {
                    for (const c of commentMap[key]) {
                        const commentTr = document.createElement("tr");
                        commentTr.className = "review-comment-row";
                        const commentTd = document.createElement("td");
                        commentTd.colSpan = 2;
                        commentTd.innerHTML =
                            `<div class="review-comment">` +
                            `<span class="review-comment-badge badge-${c.type}">${escapeHtml(c.type)}</span>` +
                            `<span class="review-comment-text">${escapeHtml(c.comment)}</span>` +
                            `</div>`;
                        commentTr.appendChild(commentTd);
                        tbody.appendChild(commentTr);
                    }
                }
            }
        }

        table.appendChild(tbody);
        fileEl.appendChild(table);
        diffContainer.appendChild(fileEl);
    }
}

// --- Logs ---
function getLogTimeSeconds(log) {
    if (typeof log.time_seconds === "number") {
        return log.time_seconds;
    }
    if (typeof log.elapsed_ms === "number") {
        return Number((log.elapsed_ms / 1000).toFixed(2));
    }
    return "—";
}

function getLogSummary(log) {
    if (typeof log.summary === "string" && log.summary.length > 0) {
        return log.summary;
    }
    if (
        log.review_json &&
        typeof log.review_json === "object" &&
        typeof log.review_json.summary === "string"
    ) {
        return log.review_json.summary;
    }
    return "—";
}

async function loadLogs() {
    console.log("Loading logs from backend...");
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/logs`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.logs.length === 0) {
            logsBody.innerHTML = '<tr><td colspan="6" class="empty-logs">No reviews yet.</td></tr>';
            console.log("No logs available");
            return;
        }
        logsBody.innerHTML = "";
        for (const log of data.logs.reverse()) {
            const timestamp = typeof log.timestamp === "string" ? log.timestamp : "—";
            const promptName = typeof log.prompt_name === "string" ? log.prompt_name : "—";
            const mrUrl = typeof log.mr_url === "string" ? log.mr_url : "—";
            const tokens =
                typeof log.tokens_used === "number" ? log.tokens_used.toLocaleString() : "—";
            const timeSeconds = getLogTimeSeconds(log);
            const summary = getLogSummary(log);

            const tr = document.createElement("tr");
            tr.innerHTML =
                `<td title="${escapeHtml(timestamp)}">${escapeHtml(timestamp)}</td>` +
                `<td>${escapeHtml(promptName)}</td>` +
                `<td title="${escapeHtml(mrUrl)}">${escapeHtml(mrUrl)}</td>` +
                `<td>${tokens}</td>` +
                `<td>${escapeHtml(String(timeSeconds))}</td>` +
                `<td title="${escapeHtml(summary)}">${escapeHtml(summary)}</td>`;
            logsBody.appendChild(tr);
        }
        console.log(`Loaded ${data.logs.length} logs`);
    } catch (e) {
        console.error("Failed to load logs:", e.message);
        logsBody.innerHTML = '<tr><td colspan="6" class="error-logs">Error loading logs: ' + escapeHtml(e.message) + '</td></tr>';
    }
}
// --- CSV ---
btnDownloadCsv.addEventListener("click", async () => {
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/logs/csv`);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "sandmark_logs.csv";
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        showError("Failed to download CSV: " + e.message);
    }
});

btnCopyCsv.addEventListener("click", async () => {
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/logs/csv`);
        const text = await res.text();
        await navigator.clipboard.writeText(text);
        btnCopyCsv.textContent = "Copied!";
        setTimeout(() => { btnCopyCsv.textContent = "Copy CSV"; }, 2000);
    } catch (e) {
        showError("Failed to copy CSV: " + e.message);
    }
});

// --- Init ---
console.log("SANDMARK initializing...");
setActivePromptTab("select");
// Load prompts and logs
Promise.all([
    loadPrompts().catch(e => console.error("Prompt load failed:", e)),
    loadLogs().catch(e => console.error("Logs load failed:", e))
]).finally(() => {
    console.log("SANDMARK initialization complete");
});
