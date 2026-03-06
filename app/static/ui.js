const scenarioTableBody = document.querySelector("#scenario-table tbody");
const runsTableBody = document.querySelector("#runs-table tbody");
const scenarioSelect = document.getElementById("scenario-name");
const mapInput = document.getElementById("map-name");
const timeoutInput = document.getElementById("timeout-seconds");
const fixedDeltaInput = document.getElementById("fixed-delta");
const viewerFriendlyInput = document.getElementById("viewer-friendly");
const createForm = document.getElementById("create-form");
const createResult = document.getElementById("create-result");
const refreshRunsButton = document.getElementById("refresh-runs");
const eventsRunIdInput = document.getElementById("events-run-id");
const loadEventsButton = document.getElementById("load-events");
const eventsResult = document.getElementById("events-result");

let scenarioTemplates = {};

async function apiGet(url) {
  const resp = await fetch(url);
  const data = await resp.json();
  if (!resp.ok || !data.success) {
    throw new Error(data?.detail?.message || data?.error?.message || "接口请求失败");
  }
  return data.data;
}

async function apiPost(url, payload = null) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload ? JSON.stringify(payload) : null,
  });

  const data = await resp.json();
  if (!resp.ok || !data.success) {
    throw new Error(data?.detail?.message || data?.error?.message || "接口请求失败");
  }
  return data.data;
}

function renderScenarioTable(scenarios) {
  scenarioTableBody.innerHTML = "";
  scenarioSelect.innerHTML = "";

  scenarios.forEach((scenario) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${scenario.display_name} <code>(${scenario.scenario_name})</code></td>
      <td>${scenario.description}</td>
      <td>${scenario.default_map_name}</td>
    `;
    scenarioTableBody.appendChild(tr);

    const option = document.createElement("option");
    option.value = scenario.scenario_name;
    option.textContent = `${scenario.display_name} (${scenario.scenario_name})`;
    scenarioSelect.appendChild(option);

    scenarioTemplates[scenario.scenario_name] = scenario.descriptor_template;
  });

  if (scenarioSelect.options.length > 0) {
    applyScenarioDefaults(scenarioSelect.value);
  }
}

function applyScenarioDefaults(scenarioName) {
  const template = scenarioTemplates[scenarioName];
  if (!template) {
    return;
  }

  mapInput.value = template.map_name;
  timeoutInput.value = template.termination.timeout_seconds;
  fixedDeltaInput.value = template.sync.fixed_delta_seconds;
  viewerFriendlyInput.checked = Boolean(template.debug?.viewer_friendly);
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined) {
    return "-";
  }
  return Number(value).toFixed(digits);
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return value;
}

function renderRuns(runs) {
  runsTableBody.innerHTML = "";

  runs.forEach((run) => {
    const tr = document.createElement("tr");

    const actions = document.createElement("div");
    actions.className = "actions";

    const startBtn = document.createElement("button");
    startBtn.textContent = "启动";
    startBtn.onclick = () => runAction(run.run_id, "start");

    const stopBtn = document.createElement("button");
    stopBtn.textContent = "停止";
    stopBtn.onclick = () => runAction(run.run_id, "stop");

    const cancelBtn = document.createElement("button");
    cancelBtn.textContent = "取消";
    cancelBtn.onclick = () => runAction(run.run_id, "cancel");

    const refreshBtn = document.createElement("button");
    refreshBtn.textContent = "刷新状态";
    refreshBtn.onclick = () => refreshSingleRun(run.run_id);

    const eventsBtn = document.createElement("button");
    eventsBtn.textContent = "查看事件";
    eventsBtn.onclick = () => {
      eventsRunIdInput.value = run.run_id;
      loadEvents(run.run_id);
    };

    [startBtn, stopBtn, cancelBtn, refreshBtn, eventsBtn].forEach((btn) => actions.appendChild(btn));

    tr.innerHTML = `
      <td><code>${run.run_id}</code></td>
      <td>${run.scenario_name}</td>
      <td>${formatValue(run.map_name)}</td>
      <td>${run.status}</td>
      <td>${formatValue(run.started_at_utc)}</td>
      <td>${formatValue(run.ended_at_utc)}</td>
      <td>${formatNumber(run.sim_time, 3)}</td>
      <td>${formatValue(run.current_tick)}</td>
      <td>${formatNumber(run.wall_elapsed_seconds, 3)}</td>
      <td>${formatValue(run.spawned_actors_count)}</td>
      <td>${run.error_reason || "-"}</td>
      <td></td>
    `;
    tr.children[11].appendChild(actions);

    runsTableBody.appendChild(tr);
  });
}

async function loadScenarios() {
  const data = await apiGet("/scenarios");
  renderScenarioTable(data.builtins || []);
}

async function loadRuns() {
  const runs = await apiGet("/runs");
  renderRuns(runs || []);
}

async function refreshSingleRun(runId) {
  await apiGet(`/runs/${runId}`);
  await loadRuns();
}

async function runAction(runId, action) {
  try {
    const result = await apiPost(`/runs/${runId}/${action}`);
    createResult.textContent = JSON.stringify(result, null, 2);
    await loadRuns();
  } catch (error) {
    createResult.textContent = `操作失败: ${error.message}`;
  }
}

function buildDescriptorFromForm() {
  const scenarioName = scenarioSelect.value;
  const template = scenarioTemplates[scenarioName];
  if (!template) {
    throw new Error("未找到场景模板");
  }

  const descriptor = JSON.parse(JSON.stringify(template));
  descriptor.map_name = mapInput.value.trim();
  descriptor.termination.timeout_seconds = Number.parseInt(timeoutInput.value, 10);
  descriptor.sync.fixed_delta_seconds = Number.parseFloat(fixedDeltaInput.value);

  descriptor.debug = descriptor.debug || {};
  descriptor.debug.viewer_friendly = viewerFriendlyInput.checked;

  descriptor.metadata = descriptor.metadata || {};
  descriptor.metadata.author = "web-ui";
  descriptor.metadata.tags = ["ui", scenarioName];
  descriptor.metadata.description = "由中文最小控制台创建";

  return descriptor;
}

async function createRun(event) {
  event.preventDefault();

  try {
    const descriptor = buildDescriptorFromForm();
    const run = await apiPost("/runs", { descriptor });
    createResult.textContent = `创建成功:\n${JSON.stringify(run, null, 2)}`;
    await loadRuns();
  } catch (error) {
    createResult.textContent = `创建失败: ${error.message}`;
  }
}

async function loadEvents(runId) {
  const targetRunId = runId || eventsRunIdInput.value.trim();
  if (!targetRunId) {
    eventsResult.textContent = "请先输入 run_id";
    return;
  }

  try {
    const events = await apiGet(`/runs/${targetRunId}/events`);
    const sorted = [...events].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    );
    eventsResult.textContent = JSON.stringify(sorted, null, 2);
  } catch (error) {
    eventsResult.textContent = `读取事件失败: ${error.message}`;
  }
}

async function bootstrap() {
  await loadScenarios();
  await loadRuns();
}

scenarioSelect.addEventListener("change", (event) => {
  applyScenarioDefaults(event.target.value);
});
createForm.addEventListener("submit", createRun);
refreshRunsButton.addEventListener("click", loadRuns);
loadEventsButton.addEventListener("click", () => loadEvents());

bootstrap().catch((error) => {
  createResult.textContent = `初始化失败: ${error.message}`;
});
