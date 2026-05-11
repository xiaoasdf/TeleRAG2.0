const STATUS_LABELS = {
  pending: "等待中",
  running: "构建中",
  ready: "可用",
  failed: "失败",
};

let selectedFiles = [];

async function postFormData(url, formData) {
  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "请求失败");
  }
  return payload;
}

async function postJson(url, data) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "请求失败");
  }
  return payload;
}

async function deleteRequest(url) {
  const response = await fetch(url, { method: "DELETE" });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "删除失败");
  }
  return payload;
}

function renderSources(sources) {
  const container = document.getElementById("sources");
  if (!container) {
    return;
  }
  if (!sources.length) {
    container.innerHTML = "<p class=\"muted\">未返回来源。</p>";
    return;
  }
  container.innerHTML = sources.map((source) => {
    const location = source.page ? `${source.source} (page ${source.page})` : source.source;
    return `
      <article class="source-card">
        <div class="row">
          <strong>${location}</strong>
          <span class="muted">score=${source.score.toFixed(4)}</span>
        </div>
        <p class="muted">${source.chunk_id}</p>
        <p>${source.snippet}</p>
      </article>
    `;
  }).join("");
}

function formatBytes(bytes) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderSelectedFiles() {
  const list = document.getElementById("selected-file-list");
  const count = document.getElementById("selected-file-count");
  if (!list || !count) {
    return;
  }
  if (!selectedFiles.length) {
    list.innerHTML = "<p class=\"muted\">暂未选择文件。</p>";
    count.textContent = "还未选择文件";
    return;
  }
  count.textContent = `已选择 ${selectedFiles.length} 个文件`;
  list.innerHTML = selectedFiles.map((file, index) => `
    <div class="file-row">
      <div class="file-meta">
        <div class="file-name">${file.name}</div>
        <div class="file-size">${formatBytes(file.size)}</div>
      </div>
      <button type="button" class="danger remove-file-button" data-file-index="${index}">移除</button>
    </div>
  `).join("");
}

async function initCreateKbForm() {
  const form = document.getElementById("create-kb-form");
  if (!form) {
    return;
  }
  const message = document.getElementById("create-kb-message");
  const pickButton = document.getElementById("pick-files-button");
  const hiddenInput = document.getElementById("hidden-file-input");

  renderSelectedFiles();

  pickButton?.addEventListener("click", () => hiddenInput?.click());
  hiddenInput?.addEventListener("change", () => {
    const incomingFiles = Array.from(hiddenInput.files || []);
    selectedFiles = selectedFiles.concat(incomingFiles);
    hiddenInput.value = "";
    renderSelectedFiles();
  });

  form.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    if (!target.classList.contains("remove-file-button")) {
      return;
    }
    const index = Number(target.dataset.fileIndex);
    selectedFiles.splice(index, 1);
    renderSelectedFiles();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selectedFiles.length) {
      message.textContent = "请先选择至少一个文件。";
      return;
    }
    message.textContent = "正在上传文件并创建知识库...";
    const formData = new FormData();
    const name = form.querySelector('input[name="name"]').value;
    formData.append("name", name);
    selectedFiles.forEach((file) => {
      formData.append("files", file, file.name);
    });
    try {
      const payload = await postFormData("/knowledge-bases", formData);
      window.location.href = `/kb/${payload.kb_id}`;
    } catch (error) {
      message.textContent = error.message;
    }
  });
}

async function pollStatus(kbId) {
  const statusNode = document.getElementById("kb-status");
  const errorNode = document.getElementById("kb-error");
  const queryMessage = document.getElementById("query-message");
  const form = document.getElementById("query-form");
  if (!statusNode || !form) {
    return;
  }

  const poll = async () => {
    const response = await fetch(`/knowledge-bases/${kbId}/status`);
    const payload = await response.json();
    if (!response.ok) {
      return;
    }
    statusNode.textContent = STATUS_LABELS[payload.status] || payload.status;
    statusNode.className = `status status-${payload.status}`;
    if (errorNode) {
      errorNode.textContent = payload.error_message || "";
    }
    const ready = payload.status === "ready";
    form.querySelector("textarea").disabled = !ready;
    form.querySelector("button").disabled = !ready;
    if (queryMessage) {
      queryMessage.textContent = ready ? "知识库已可用。" : "当前知识库仍在构建中，页面会自动刷新状态。";
    }
    if (!ready && payload.status !== "failed") {
      window.setTimeout(poll, 2000);
    }
  };

  await poll();
}

async function initQueryForm() {
  const body = document.body;
  const kbId = body.dataset.kbId;
  const form = document.getElementById("query-form");
  if (!kbId || !form) {
    return;
  }

  if (document.getElementById("kb-status")?.textContent !== "ready") {
    pollStatus(kbId);
  }

  const answer = document.getElementById("answer");
  const thinking = document.getElementById("thinking");
  const message = document.getElementById("query-message");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = form.querySelector("textarea").value.trim();
    if (!question) {
      message.textContent = "问题不能为空。";
      return;
    }
    message.textContent = "正在生成回答...";
    try {
      const payload = await postJson(`/knowledge-bases/${kbId}/query`, { question });
      answer.textContent = payload.answer;
      thinking.textContent = payload.thinking ? `思考过程\n${payload.thinking}` : "";
      renderSources(payload.sources);
      message.textContent = "回答已生成。";
    } catch (error) {
      message.textContent = error.message;
    }
  });
}

function initDeleteButtons() {
  document.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement) || !target.classList.contains("delete-kb-button")) {
      return;
    }
    const kbId = target.dataset.kbId;
    const kbName = target.dataset.kbName || "该知识库";
    if (!kbId) {
      return;
    }
    const confirmed = window.confirm(`确认删除知识库“${kbName}”吗？该操作不可恢复。`);
    if (!confirmed) {
      return;
    }
    try {
      await deleteRequest(`/knowledge-bases/${kbId}`);
      if (document.body.dataset.kbId === kbId) {
        window.location.href = "/";
        return;
      }
      window.location.reload();
    } catch (error) {
      window.alert(error.message);
    }
  });
}

initCreateKbForm();
initQueryForm();
initDeleteButtons();
