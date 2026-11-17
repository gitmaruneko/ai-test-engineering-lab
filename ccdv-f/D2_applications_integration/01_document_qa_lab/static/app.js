const byId = (id) => document.getElementById(id);
const storageKey = "ccdvf-d2-session";
let activeSession = null;
let busy = false;

function renderControls() {
  byId("file").disabled = busy;
  byId("upload-button").disabled = busy || !byId("file").files.length;
  byId("restart").disabled = busy || !activeSession;
  byId("question").disabled = busy || !activeSession;
  byId("ask-button").disabled = busy || !activeSession;
}

function setBusy(value) {
  busy = value;
  renderControls();
}

function showError(id, message = "") {
  const node = byId(id);
  node.textContent = message;
  node.hidden = !message;
}

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === "string" ? error.detail : `請求失敗 (${response.status})`);
  }
  return response;
}

function sessionUrl() {
  return `/api/sessions/${encodeURIComponent(activeSession.id)}`;
}

function updateDocument() {
  byId("session").hidden = !activeSession;
  if (!activeSession) return;
  byId("document-name").textContent = activeSession.name;
  const { section_count: sections, total_turns: turns, summarized_turns: summarized } = activeSession;
  byId("document-info").textContent = `${sections} 個段落 · ${turns} 輪問答 · ${summarized} 輪已壓縮`;
}

function createTurn(question) {
  const item = document.createElement("li");
  item.className = "turn";
  const heading = document.createElement("h3");
  heading.textContent = question;
  const answer = document.createElement("p");
  answer.className = "answer";
  item.append(heading, answer);
  byId("turns").append(item);
  byId("empty").hidden = true;
  return { item, answer };
}

function finishTurn(view, turn) {
  view.answer.textContent = turn.answer;
  const meta = document.createElement("div");
  meta.className = "meta";
  for (const citation of turn.citations) {
    const details = document.createElement("details");
    const label = document.createElement("summary");
    label.textContent = `引用段落 ${citation.section}`;
    const text = document.createElement("p");
    text.className = "citation-text";
    text.textContent = citation.excerpt;
    details.append(label, text);
    meta.append(details);
  }
  if (turn.evidence === "insufficient") {
    const status = document.createElement("p");
    status.textContent = "文件證據不足";
    meta.append(status);
  }
  if (turn.usage) {
    const metrics = document.createElement("p");
    const usage = turn.usage;
    metrics.textContent = `Token · 一般輸入 ${usage.input_tokens} · 寫入快取 ${usage.cache_creation_input_tokens} · 讀取快取 ${usage.cache_read_input_tokens} · 輸出 ${usage.output_tokens}`;
    meta.append(metrics);
  }
  view.item.append(meta);
}

function setSession(session) {
  activeSession = session;
  localStorage.setItem(storageKey, session.id);
  showError("question-error");
  byId("question").value = "";
  byId("turns").replaceChildren();
  byId("empty").textContent = "可以開始對這份文件提問。";
  byId("empty").hidden = Boolean(session.recent.length);
  for (const turn of session.recent) finishTurn(createTurn(turn.question), turn);
  updateDocument();
  renderControls();
}

byId("file").addEventListener("change", renderControls);
byId("upload").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = byId("file").files[0];
  if (busy || !file) return;
  setBusy(true);
  showError("upload-error");
  try {
    const response = await request("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "text/plain", "X-Document-Name": encodeURIComponent(file.name) },
      body: file,
    });
    setSession(await response.json());
    byId("file").value = "";
  } catch (error) {
    showError("upload-error", error.message);
  } finally {
    setBusy(false);
  }
});

byId("restart").addEventListener("click", async () => {
  if (busy || !activeSession) return;
  setBusy(true);
  showError("upload-error");
  try {
    const response = await request(`${sessionUrl()}/restart`, { method: "POST" });
    setSession(await response.json());
  } catch (error) {
    showError("upload-error", error.message);
  } finally {
    setBusy(false);
  }
});

async function consumeAnswer(response, update) {
  const decoder = new TextDecoder();
  const reader = response.body.getReader();
  let buffer = "";
  let final = null;
  try {
    while (!final) {
      const { done, value } = await reader.read();
      if (done) throw new Error("串流在答案完成前中斷，請再試一次。");
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line) continue;
        const event = JSON.parse(line);
        if (event.event === "error") throw new Error(event.message);
        if (event.event === "delta") update(event.text);
        if (event.event === "done") {
          final = event;
          break;
        }
      }
    }
    return final;
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

byId("ask").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = byId("question");
  const question = input.value.trim();
  if (busy || !activeSession || !question) return;
  const view = createTurn(question);
  setBusy(true);
  showError("question-error");
  byId("question-status").textContent = "正在回答…";
  try {
    const response = await request(`${sessionUrl()}/questions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const result = await consumeAnswer(response, (text) => view.answer.append(text));
    finishTurn(view, result.turn);
    input.value = "";
    activeSession.total_turns = result.total_turns;
    activeSession.summarized_turns = result.summarized_turns;
    const turns = byId("turns");
    while (turns.children.length > result.retained_turns) turns.firstElementChild.remove();
    updateDocument();
  } catch (error) {
    view.item.remove();
    byId("empty").hidden = Boolean(byId("turns").children.length);
    showError("question-error", error.message);
  } finally {
    byId("question-status").textContent = "";
    setBusy(false);
    input.focus();
  }
});

async function initialize() {
  setBusy(true);
  try {
    const config = await (await request("/api/config")).json();
    byId("mode").textContent = config.mode === "claude"
      ? `${config.model} · Prompt ${config.prompt_version}`
      : "離線模式 · 關鍵字擷取";
    byId("file-help").textContent = `UTF-8 · Markdown 或純文字 · ${config.max_document_bytes / 1024} KiB 上限`;
    const savedId = localStorage.getItem(storageKey);
    if (savedId) {
      const response = await fetch(`/api/sessions/${encodeURIComponent(savedId)}`);
      if (response.ok) setSession(await response.json());
      else if (response.status === 404) localStorage.removeItem(storageKey);
      else throw new Error("無法載入先前的對話。");
    }
  } catch (error) {
    showError("upload-error", error.message);
  } finally {
    setBusy(false);
  }
}

initialize();
