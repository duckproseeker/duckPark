const scenarioTableBody = document.querySelector("#scenario-table tbody");
const gatewayTableBody = document.querySelector("#gateway-table tbody");
const activeRunsTableBody = document.querySelector("#active-runs-table tbody");
const historyRunsTableBody = document.querySelector("#history-runs-table tbody");
const activeRunsCount = document.getElementById("active-runs-count");
const historyRunsCount = document.getElementById("history-runs-count");
const historyRunsPanel = document.getElementById("history-runs-panel");
const scenarioSelect = document.getElementById("scenario-name");
const gatewaySelect = document.getElementById("gateway-id");
const mapSelect = document.getElementById("map-name");
const videoSourceSelect = document.getElementById("video-source");
const evaluationProfileSelect = document.getElementById("evaluation-profile");
const mapFieldNote = document.getElementById("map-field-note");
const timeoutInput = document.getElementById("timeout-seconds");
const fixedDeltaInput = document.getElementById("fixed-delta");
const viewerFriendlyInput = document.getElementById("viewer-friendly");
const createForm = document.getElementById("create-form");
const createRunButton = document.getElementById("create-run-button");
const createResult = document.getElementById("create-result");
const refreshGatewaysButton = document.getElementById("refresh-gateways");
const refreshRunsButton = document.getElementById("refresh-runs");

const detailBackdrop = document.getElementById("detail-backdrop");
const runDetailDrawer = document.getElementById("run-detail-drawer");
const closeDetailButton = document.getElementById("close-detail");
const detailRefreshButton = document.getElementById("detail-refresh");
const detailRunTitle = document.getElementById("detail-run-title");
const detailSummary = document.getElementById("detail-summary");
const detailFlags = document.getElementById("detail-flags");
const detailError = document.getElementById("detail-error");
const detailTabOverviewButton = document.getElementById("detail-tab-overview");
const detailTabEventsButton = document.getElementById("detail-tab-events");
const detailPanelOverview = document.getElementById("detail-panel-overview");
const detailPanelEvents = document.getElementById("detail-panel-events");
const eventsState = document.getElementById("events-state");
const eventsTimeline = document.getElementById("events-timeline");

const FINAL_STATUSES = new Set(["COMPLETED", "FAILED", "CANCELED"]);
const ACTIVE_STATUSES = new Set(["CREATED", "QUEUED", "STARTING", "RUNNING", "PAUSED", "STOPPING"]);
const TAB_NODES = {
  overview: {
    button: detailTabOverviewButton,
    panel: detailPanelOverview,
  },
  events: {
    button: detailTabEventsButton,
    panel: detailPanelEvents,
  },
};

let scenarioTemplates = {};
let availableMaps = [];
let gatewayIndex = new Map();
let evaluationProfileIndex = new Map();
let runIndex = new Map();
let eventCache = new Map();
let selectedRunId = null;
let selectedTab = "overview";

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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toFixed(digits);
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString("zh-CN", { hour12: false });
}

function getStatusTone(status) {
  if (status === "RUNNING" || status === "COMPLETED") {
    return "success";
  }
  if (status === "FAILED" || status === "CANCELED") {
    return "danger";
  }
  if (status === "STOPPING" || status === "STARTING") {
    return "warning";
  }
  return "neutral";
}

function renderScenarioTable(scenarios) {
  scenarioTableBody.innerHTML = "";
  scenarioSelect.innerHTML = "";
  createRunButton.disabled = scenarios.length === 0;

  scenarios.forEach((scenario) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(scenario.display_name)} <code>(${escapeHtml(scenario.scenario_name)})</code></td>
      <td>${escapeHtml(scenario.description)}</td>
      <td>${escapeHtml(scenario.default_map_name)}</td>
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

function renderMapOptions(maps) {
  availableMaps = maps;
  mapSelect.innerHTML = "";

  if (!maps.length) {
    mapSelect.disabled = true;
    mapFieldNote.textContent =
      "当前未读取到 CARLA 地图列表；ScenarioRunner 会按场景模板中的锁定地图执行。";

    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = "由场景模板锁定";
    mapSelect.appendChild(emptyOption);
    return;
  }

  maps.forEach((mapItem) => {
    const option = document.createElement("option");
    option.value = mapItem.map_name;
    option.textContent = mapItem.display_name;
    option.dataset.displayName = mapItem.display_name;
    mapSelect.appendChild(option);
  });

  mapSelect.disabled = true;
  mapFieldNote.textContent =
    "地图由官方 OpenSCENARIO 模板锁定，这里只展示当前 CARLA 可见地图。";
}

function renderGatewayOptions(gateways) {
  const previousValue = gatewaySelect.value;
  gatewaySelect.innerHTML = '<option value="">未绑定网关（保留纯 CARLA 模式）</option>';

  gateways.forEach((gateway) => {
    const option = document.createElement("option");
    option.value = gateway.gateway_id;
    option.textContent = `${gateway.name} (${gateway.gateway_id})`;
    gatewaySelect.appendChild(option);
  });

  if (previousValue && gatewayIndex.has(previousValue)) {
    gatewaySelect.value = previousValue;
  }
}

function renderGatewayTable(gateways) {
  gatewayTableBody.innerHTML = "";
  gatewayIndex = new Map(gateways.map((gateway) => [gateway.gateway_id, gateway]));
  renderGatewayOptions(gateways);

  if (!gateways.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="5" class="empty-state">当前还没有已注册的网关。</td>';
    gatewayTableBody.appendChild(tr);
    return;
  }

  gateways.forEach((gateway) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <div class="gateway-cell">
          <strong>${escapeHtml(gateway.name)}</strong>
          <code>${escapeHtml(gateway.gateway_id)}</code>
          <span class="run-meta">${escapeHtml(formatValue(gateway.address))}</span>
        </div>
      </td>
      <td>
        <span class="status-badge tone-${getStatusTone(gateway.status)}">${escapeHtml(gateway.status)}</span>
      </td>
      <td>
        <div class="gateway-capabilities">
          <span class="metric-pill">输入 ${escapeHtml(formatValue(gateway.capabilities?.video_input_modes?.join(", ")))}</span>
          <span class="metric-pill">输出 ${escapeHtml(formatValue(gateway.capabilities?.dut_output_modes?.join(", ")))}</span>
        </div>
      </td>
      <td>
        <div class="stack-list">
          <span><strong>最近心跳</strong> ${escapeHtml(formatDateTime(gateway.last_heartbeat_at_utc))}</span>
          <span><strong>更新时间</strong> ${escapeHtml(formatDateTime(gateway.updated_at_utc))}</span>
        </div>
      </td>
      <td>
        <div class="metric-group">
          <span class="metric-pill">输入 FPS ${escapeHtml(formatNumber(gateway.metrics?.input_fps, 2))}</span>
          <span class="metric-pill">输出 FPS ${escapeHtml(formatNumber(gateway.metrics?.output_fps, 2))}</span>
          <span class="metric-pill">丢帧 ${escapeHtml(formatNumber(gateway.metrics?.frame_drop_rate, 4))}</span>
        </div>
      </td>
    `;
    gatewayTableBody.appendChild(tr);
  });
}

function renderEvaluationProfiles(profiles) {
  const previousValue = evaluationProfileSelect.value;
  evaluationProfileIndex = new Map(profiles.map((profile) => [profile.profile_name, profile]));
  evaluationProfileSelect.innerHTML = '<option value="">未绑定评测模板</option>';

  profiles.forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.profile_name;
    option.textContent = `${profile.display_name} (${profile.profile_name})`;
    evaluationProfileSelect.appendChild(option);
  });

  if (previousValue && evaluationProfileIndex.has(previousValue)) {
    evaluationProfileSelect.value = previousValue;
  } else if (profiles.length > 0) {
    evaluationProfileSelect.value = profiles[0].profile_name;
  }
}

function selectMapOption(preferredMapName) {
  if (!availableMaps.length) {
    return;
  }

  const exactMatch = availableMaps.find((mapItem) => mapItem.map_name === preferredMapName);
  const shortNameMatch = availableMaps.find(
    (mapItem) => mapItem.display_name === preferredMapName,
  );
  const target = exactMatch || shortNameMatch || availableMaps[0];
  mapSelect.value = target.map_name;
}

function applyScenarioDefaults(scenarioName) {
  const template = scenarioTemplates[scenarioName];
  if (!template) {
    return;
  }

  const lockedMapName = template.map_name || "";
  selectMapOption(lockedMapName);
  if (mapSelect.value !== lockedMapName) {
    mapSelect.innerHTML = "";
    const option = document.createElement("option");
    option.value = lockedMapName;
    option.textContent = lockedMapName || "由场景模板锁定";
    mapSelect.appendChild(option);
    mapSelect.value = lockedMapName;
  }
  timeoutInput.value = template.termination.timeout_seconds;
  fixedDeltaInput.value = template.sync.fixed_delta_seconds;
  viewerFriendlyInput.checked = false;
  viewerFriendlyInput.disabled = true;
}

function createFlag(label, active) {
  const badge = document.createElement("span");
  badge.className = `flag-badge ${active ? "is-on" : "is-off"}`;
  badge.textContent = `${label}: ${active ? "是" : "否"}`;
  return badge;
}

function createSummaryItem(label, value, emphasize = false) {
  const block = document.createElement("div");
  block.className = "summary-item";

  const labelNode = document.createElement("span");
  labelNode.className = "summary-label";
  labelNode.textContent = label;

  const valueNode = document.createElement("strong");
  valueNode.className = emphasize ? "summary-value emphasize" : "summary-value";
  valueNode.textContent = value;

  block.appendChild(labelNode);
  block.appendChild(valueNode);
  return block;
}

function renderDetailOverview(run) {
  detailSummary.innerHTML = "";
  detailFlags.innerHTML = "";

  if (!run) {
    detailRunTitle.textContent = "未选择运行";
    detailSummary.appendChild(createSummaryItem("状态", "-"));
    detailSummary.appendChild(createSummaryItem("场景", "-"));
    detailSummary.appendChild(createSummaryItem("地图", "-"));
    detailError.textContent = "-";
    detailFlags.appendChild(createFlag("stop_requested", false));
    detailFlags.appendChild(createFlag("cancel_requested", false));
    return;
  }

  detailRunTitle.textContent = `${run.scenario_name} · ${run.run_id}`;
  detailSummary.appendChild(createSummaryItem("状态", run.status, true));
  detailSummary.appendChild(createSummaryItem("场景", run.scenario_name));
  detailSummary.appendChild(createSummaryItem("地图", formatValue(run.map_name)));
  detailSummary.appendChild(
    createSummaryItem("网关", formatValue(run.hil_config?.gateway_id)),
  );
  detailSummary.appendChild(
    createSummaryItem("视频源", formatValue(run.hil_config?.video_source)),
  );
  detailSummary.appendChild(
    createSummaryItem(
      "评测模板",
      formatValue(run.evaluation_profile?.profile_name),
    ),
  );
  detailSummary.appendChild(createSummaryItem("开始时间", formatDateTime(run.started_at_utc)));
  detailSummary.appendChild(createSummaryItem("结束时间", formatDateTime(run.ended_at_utc)));
  detailSummary.appendChild(createSummaryItem("仿真时间", `${formatNumber(run.sim_time, 3)} s`));
  detailSummary.appendChild(createSummaryItem("当前 Tick", formatValue(run.current_tick)));
  detailSummary.appendChild(
    createSummaryItem("墙钟耗时", `${formatNumber(run.wall_elapsed_seconds, 3)} s`),
  );
  detailSummary.appendChild(
    createSummaryItem("Actors 数量", formatValue(run.spawned_actors_count)),
  );

  detailFlags.appendChild(createFlag("stop_requested", Boolean(run.stop_requested)));
  detailFlags.appendChild(createFlag("cancel_requested", Boolean(run.cancel_requested)));
  detailError.textContent = run.error_reason || "-";
}

function renderEventsTimeline(events) {
  eventsTimeline.innerHTML = "";

  if (!events.length) {
    eventsState.textContent = "当前运行还没有事件记录。";
    return;
  }

  eventsState.textContent = `共 ${events.length} 条事件，按时间倒序展示。`;

  events.forEach((event) => {
    const item = document.createElement("article");
    item.className = `event-item level-${String(event.level || "INFO").toLowerCase()}`;

    const header = document.createElement("div");
    header.className = "event-head";

    const typeNode = document.createElement("strong");
    typeNode.textContent = event.event_type || "UNKNOWN";

    const metaNode = document.createElement("span");
    metaNode.className = "event-meta";
    metaNode.textContent = `${formatDateTime(event.timestamp)} · ${formatValue(event.level)}`;

    header.appendChild(typeNode);
    header.appendChild(metaNode);

    const messageNode = document.createElement("p");
    messageNode.className = "event-message";
    messageNode.textContent = event.message || "-";

    item.appendChild(header);
    item.appendChild(messageNode);

    if (event.payload && Object.keys(event.payload).length > 0) {
      const payloadDetails = document.createElement("details");
      payloadDetails.className = "event-payload";

      const summary = document.createElement("summary");
      summary.textContent = "查看 payload";

      const pre = document.createElement("pre");
      pre.className = "result compact-result";
      pre.textContent = JSON.stringify(event.payload, null, 2);

      payloadDetails.appendChild(summary);
      payloadDetails.appendChild(pre);
      item.appendChild(payloadDetails);
    }

    eventsTimeline.appendChild(item);
  });
}

function setDrawerVisible(visible) {
  runDetailDrawer.classList.toggle("is-open", visible);
  runDetailDrawer.setAttribute("aria-hidden", String(!visible));
  detailBackdrop.hidden = !visible;
  detailBackdrop.classList.toggle("is-visible", visible);
  document.body.classList.toggle("drawer-open", visible);
}

function setActiveTab(tabName) {
  selectedTab = tabName;

  Object.entries(TAB_NODES).forEach(([name, nodes]) => {
    const active = name === tabName;
    nodes.button.classList.toggle("is-active", active);
    nodes.panel.classList.toggle("is-active", active);
  });

  if (tabName === "events" && selectedRunId) {
    loadEvents(selectedRunId).catch((error) => {
      eventsState.textContent = `读取事件失败: ${error.message}`;
    });
  }
}

function updateSelectedRow() {
  const rows = document.querySelectorAll("tr[data-run-id]");
  rows.forEach((row) => {
    row.classList.toggle("is-selected", row.dataset.runId === selectedRunId);
  });
}

function openRunDetail(runId, tabName = "overview") {
  selectedRunId = runId;
  renderDetailOverview(runIndex.get(runId) || null);
  updateSelectedRow();
  setDrawerVisible(true);
  setActiveTab(tabName);
}

function closeRunDetail() {
  selectedRunId = null;
  updateSelectedRow();
  setDrawerVisible(false);
  renderDetailOverview(null);
  eventsState.textContent = "选择一个运行后再查看事件流。";
  eventsTimeline.innerHTML = "";
}

function renderRunRow(run) {
  const tr = document.createElement("tr");
  tr.dataset.runId = run.run_id;

  const runCell = document.createElement("td");
  const gatewayLabel = run.hil_config?.gateway_id
    ? ` · 网关：${escapeHtml(run.hil_config.gateway_id)}`
    : "";
  runCell.innerHTML = `
    <div class="run-cell">
      <strong class="run-title">${escapeHtml(run.scenario_name)}</strong>
      <code class="run-id">${escapeHtml(run.run_id)}</code>
      <span class="run-meta">地图：${escapeHtml(formatValue(run.map_name))}${gatewayLabel}</span>
    </div>
  `;

  const statusCell = document.createElement("td");
  statusCell.innerHTML = `
    <div class="status-cell">
      <span class="status-badge tone-${getStatusTone(run.status)}">${escapeHtml(run.status)}</span>
      <span class="status-note">${
        run.error_reason ? escapeHtml(run.error_reason) : "无异常"
      }</span>
    </div>
  `;

  const timeCell = document.createElement("td");
  timeCell.innerHTML = `
    <div class="stack-list">
      <span><strong>开始</strong> ${escapeHtml(formatDateTime(run.started_at_utc))}</span>
      <span><strong>结束</strong> ${escapeHtml(formatDateTime(run.ended_at_utc))}</span>
    </div>
  `;

  const metricsCell = document.createElement("td");
  metricsCell.innerHTML = `
    <div class="metric-group">
      <span class="metric-pill">Sim ${escapeHtml(formatNumber(run.sim_time, 3))} s</span>
      <span class="metric-pill">Tick ${escapeHtml(formatValue(run.current_tick))}</span>
      <span class="metric-pill">Wall ${escapeHtml(formatNumber(run.wall_elapsed_seconds, 3))} s</span>
      <span class="metric-pill">Actors ${escapeHtml(formatValue(run.spawned_actors_count))}</span>
    </div>
  `;

  const actionsCell = document.createElement("td");
  const actions = document.createElement("div");
  actions.className = "actions";

  const startBtn = document.createElement("button");
  startBtn.textContent = "启动";
  startBtn.disabled = run.status !== "CREATED";
  startBtn.onclick = async (event) => {
    event.stopPropagation();
    await runAction(run.run_id, "start");
  };

  const stopBtn = document.createElement("button");
  stopBtn.textContent = "停止";
  stopBtn.disabled = FINAL_STATUSES.has(run.status);
  stopBtn.onclick = async (event) => {
    event.stopPropagation();
    await runAction(run.run_id, "stop");
  };

  const cancelBtn = document.createElement("button");
  cancelBtn.textContent = "取消";
  cancelBtn.disabled = FINAL_STATUSES.has(run.status);
  cancelBtn.onclick = async (event) => {
    event.stopPropagation();
    await runAction(run.run_id, "cancel");
  };

  const detailBtn = document.createElement("button");
  detailBtn.textContent = "详情";
  detailBtn.onclick = (event) => {
    event.stopPropagation();
    openRunDetail(run.run_id, "overview");
  };

  [startBtn, stopBtn, cancelBtn, detailBtn].forEach((button) => actions.appendChild(button));

  actionsCell.appendChild(actions);

  tr.appendChild(runCell);
  tr.appendChild(statusCell);
  tr.appendChild(timeCell);
  tr.appendChild(metricsCell);
  tr.appendChild(actionsCell);

  tr.addEventListener("click", () => openRunDetail(run.run_id, "overview"));

  if (selectedRunId === run.run_id) {
    tr.classList.add("is-selected");
  }

  return tr;
}

function getRunSortTimestamp(run) {
  const candidates = [
    run.updated_at_utc,
    run.ended_at_utc,
    run.started_at_utc,
    run.created_at_utc,
  ];
  for (const value of candidates) {
    if (!value) {
      continue;
    }
    const timestamp = new Date(value).getTime();
    if (!Number.isNaN(timestamp)) {
      return timestamp;
    }
  }
  return 0;
}

function sortRunsForDisplay(runs) {
  return [...runs].sort((left, right) => {
    const leftActive = ACTIVE_STATUSES.has(left.status);
    const rightActive = ACTIVE_STATUSES.has(right.status);
    if (leftActive !== rightActive) {
      return leftActive ? -1 : 1;
    }
    return getRunSortTimestamp(right) - getRunSortTimestamp(left);
  });
}

function renderRunTable(targetBody, runs, emptyMessage) {
  targetBody.innerHTML = "";

  if (!runs.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="5" class="empty-state">${escapeHtml(emptyMessage)}</td>`;
    targetBody.appendChild(tr);
    return;
  }

  runs.forEach((run) => targetBody.appendChild(renderRunRow(run)));
}

function renderRuns(runs) {
  runIndex = new Map(runs.map((run) => [run.run_id, run]));

  if (!runs.length) {
    activeRunsCount.textContent = "0";
    historyRunsCount.textContent = "0";
    historyRunsPanel.open = false;
    renderRunTable(activeRunsTableBody, [], "当前没有活跃运行。");
    renderRunTable(historyRunsTableBody, [], "当前还没有历史运行记录。");
    closeRunDetail();
    renderDetailOverview(null);
    return;
  }

  const sortedRuns = sortRunsForDisplay(runs);
  const activeRuns = sortedRuns.filter((run) => ACTIVE_STATUSES.has(run.status));
  const historicalRuns = sortedRuns.filter((run) => FINAL_STATUSES.has(run.status));

  activeRunsCount.textContent = String(activeRuns.length);
  historyRunsCount.textContent = String(historicalRuns.length);
  historyRunsPanel.hidden = historicalRuns.length === 0;

  renderRunTable(activeRunsTableBody, activeRuns, "当前没有活跃运行。");
  renderRunTable(historyRunsTableBody, historicalRuns, "当前还没有历史运行记录。");

  if (selectedRunId) {
    const selectedRun = runIndex.get(selectedRunId);
    if (selectedRun) {
      renderDetailOverview(selectedRun);
    } else {
      closeRunDetail();
    }
  }
}

async function loadScenarios() {
  const data = await apiGet("/scenarios");
  renderScenarioTable(data.catalog || []);
}

async function loadGateways() {
  const data = await apiGet("/gateways");
  renderGatewayTable(data.gateways || []);
}

async function loadEvaluationProfiles() {
  const data = await apiGet("/evaluation-profiles");
  renderEvaluationProfiles(data.profiles || []);
}

async function loadMaps() {
  try {
    const data = await apiGet("/maps");
    renderMapOptions(data.maps || []);

    if (scenarioSelect.value) {
      applyScenarioDefaults(scenarioSelect.value);
    }
  } catch (error) {
    availableMaps = [];
    mapSelect.innerHTML = `<option value="">地图列表读取失败</option>`;
    mapSelect.disabled = true;
    mapFieldNote.textContent =
      `地图列表读取失败，但 ScenarioRunner 仍会使用场景模板中的锁定地图: ${error.message}`;
  }
}

async function loadRuns() {
  const runs = await apiGet("/runs");
  renderRuns(runs || []);
}

async function refreshSelectedRun(forceEvents = false) {
  const currentRunId = selectedRunId;
  if (!currentRunId) {
    return;
  }

  await loadRuns();

  if (forceEvents && selectedRunId === currentRunId) {
    eventCache.delete(currentRunId);
    await loadEvents(currentRunId, true);
  }
}

async function runAction(runId, action) {
  try {
    const result = await apiPost(`/runs/${runId}/${action}`);
    createResult.textContent = JSON.stringify(result, null, 2);
    eventCache.delete(runId);
    await loadRuns();

    if (selectedRunId === runId) {
      renderDetailOverview(runIndex.get(runId) || null);
      if (selectedTab === "events") {
        await loadEvents(runId, true);
      }
    }
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
  descriptor.map_name = descriptor.map_name || mapSelect.value;
  descriptor.termination.timeout_seconds = Number.parseInt(timeoutInput.value, 10);
  descriptor.sync.fixed_delta_seconds = Number.parseFloat(fixedDeltaInput.value);

  descriptor.debug = descriptor.debug || {};
  descriptor.debug.viewer_friendly = false;

  descriptor.metadata = descriptor.metadata || {};
  descriptor.metadata.author = "web-ui";
  descriptor.metadata.tags = ["ui", scenarioName];
  descriptor.metadata.description = "由中文最小控制台创建";

  return descriptor;
}

function buildHilConfigFromForm() {
  if (!gatewaySelect.value) {
    return null;
  }

  return {
    mode: "camera_open_loop",
    gateway_id: gatewaySelect.value,
    video_source: videoSourceSelect.value,
    dut_input_mode: "uvc_camera",
    result_ingest_mode: "http_push",
  };
}

function buildEvaluationProfileFromForm() {
  if (!evaluationProfileSelect.value) {
    return null;
  }

  const profile = evaluationProfileIndex.get(evaluationProfileSelect.value);
  if (!profile) {
    return null;
  }
  return JSON.parse(JSON.stringify(profile));
}

async function createRun(event) {
  event.preventDefault();

  try {
    const descriptor = buildDescriptorFromForm();
    const hilConfig = buildHilConfigFromForm();
    const evaluationProfile = buildEvaluationProfileFromForm();
    const payload = { descriptor };
    if (hilConfig) {
      payload.hil_config = hilConfig;
    }
    if (evaluationProfile) {
      payload.evaluation_profile = evaluationProfile;
    }
    const run = await apiPost("/runs", payload);
    createResult.textContent = `创建成功:\n${JSON.stringify(run, null, 2)}`;
    await loadRuns();
  } catch (error) {
    createResult.textContent = `创建失败: ${error.message}`;
  }
}

async function loadEvents(runId, forceRefresh = false) {
  const targetRunId = runId || selectedRunId;
  if (!targetRunId) {
    eventsState.textContent = "请先选择一个运行。";
    eventsTimeline.innerHTML = "";
    return;
  }

  if (!forceRefresh && eventCache.has(targetRunId)) {
    renderEventsTimeline(eventCache.get(targetRunId));
    return;
  }

  eventsState.textContent = "正在加载事件流...";
  eventsTimeline.innerHTML = "";

  try {
    const events = await apiGet(`/runs/${targetRunId}/events`);
    const sorted = [...events].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    );
    eventCache.set(targetRunId, sorted);
    renderEventsTimeline(sorted);
  } catch (error) {
    eventsState.textContent = `读取事件失败: ${error.message}`;
  }
}

async function bootstrap() {
  renderDetailOverview(null);
  createRunButton.disabled = true;
  await loadScenarios();
  await loadMaps();
  await loadEvaluationProfiles();
  await loadGateways();
  await loadRuns();
}

scenarioSelect.addEventListener("change", (event) => {
  applyScenarioDefaults(event.target.value);
});

createForm.addEventListener("submit", createRun);
refreshGatewaysButton.addEventListener("click", () => {
  loadGateways().catch((error) => {
    createResult.textContent = `读取网关失败: ${error.message}`;
  });
});
refreshRunsButton.addEventListener("click", loadRuns);
closeDetailButton.addEventListener("click", closeRunDetail);
detailBackdrop.addEventListener("click", closeRunDetail);
detailRefreshButton.addEventListener("click", () => {
  refreshSelectedRun(selectedTab === "events").catch((error) => {
    createResult.textContent = `刷新失败: ${error.message}`;
  });
});
detailTabOverviewButton.addEventListener("click", () => setActiveTab("overview"));
detailTabEventsButton.addEventListener("click", () => setActiveTab("events"));

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && runDetailDrawer.classList.contains("is-open")) {
    closeRunDetail();
  }
});

bootstrap().catch((error) => {
  createResult.textContent = `初始化失败: ${error.message}`;
});
