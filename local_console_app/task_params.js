const TASK_PARAM_PRESETS = {
  market_snapshot_readonly: {symbol: '510300.SH', limit: 5},
  xtdata_live_readonly_smoke: {enable_xtdata: true, allow_import_xtdata: true, allow_connect_miniqmt: true, allow_real_market_data: true, symbols: '510300.SH,159915.SZ,510500.SH', period: '1d', limit: 20, allow_xttrader: false, allow_account_query: false, allow_order_submit: false},
  factor_scan: {limit: 5},
  etf_rotation_candidates: {symbol: '510300.SH', limit: 5},
  factor_strategy_dry_run: {symbol: '510300.SH', limit: 5, max_positions: 3},
  strategy_dry_run_signals: {symbol: '510300.SH', limit: 5},
  risk_gate_dry_run: {limit: 5},
  paper_trading_dry_run: {limit: 5},
  human_approval_review_dry_run: {limit: 5},
  order_preview_dry_run: {max_single_order_amount: 1000, min_lot: 100, lot_size: 100, limit: 5},
  monitoring_alert_dry_run: {limit: 5},
  account_readonly_dry_run: {enable_account_readonly: true, manual_confirmed: true, allow_import_xttrader: true, allow_connect_trade_session: true, allow_account_query: true, allow_position_query: true, account_timeout_seconds: 120, allow_order_submit: false, allow_order_cancel: false, dry_run: true, read_only: true},
};

const TASK_PRIORITY = ['xtdata_live_readonly_smoke', 'factor_scan', 'strategy_dry_run_signals', 'risk_gate_dry_run', 'paper_trading_dry_run', 'human_approval_review_dry_run', 'order_preview_dry_run', 'account_readonly_dry_run'];

const DRYRUN_WORKFLOW = [
  {taskId: 'xtdata_live_readonly_smoke', title: '1. xtdata 只读行情 smoke', reads: '/datahub/market/latest'},
  {taskId: 'factor_scan', title: '2. 多因子扫描', reads: '/research/candidates/latest'},
  {taskId: 'strategy_dry_run_signals', title: '3. 策略 dry-run 信号', reads: '/strategy/trade-intents/latest'},
  {taskId: 'risk_gate_dry_run', title: '4. Risk Gate dry-run', reads: '/risk/decisions/latest'},
  {taskId: 'paper_trading_dry_run', title: '5. Paper / Shadow dry-run', reads: '/paper-trading/orders/latest'},
  {taskId: 'human_approval_review_dry_run', title: '6. Human Approval 只读复核卡', reads: '/approval/requests/latest'},
  {taskId: 'order_preview_dry_run', title: '7. Portfolio 订单预览', reads: '/portfolio/order-preview/latest'},
];

const WORKFLOW_SNAPSHOT_ENDPOINTS = [
  ['行情样本', '/datahub/market/latest'],
  ['候选池', '/research/candidates/latest'],
  ['策略信号', '/strategy/signals/latest'],
  ['TradeIntent', '/strategy/trade-intents/latest'],
  ['风控结果', '/risk/decisions/latest'],
  ['Paper 订单', '/paper-trading/orders/latest'],
  ['人工复核卡', '/approval/requests/latest'],
  ['订单预览', '/portfolio/order-preview/latest'],
  ['资金预算', '/portfolio/budget/latest'],
];

const UNSAFE_TRUE_KEYS = new Set(['allow_order_submit', 'allow_order_cancel', 'order_submit_enabled', 'order_cancel_enabled', 'real_order_submitted', 'live_trading_enabled', 'can_submit_order']);

function taskPreset(taskId) { return TASK_PARAM_PRESETS[taskId] || {limit: 5}; }
function taskFieldType(value) { if (typeof value === 'boolean') return 'checkbox'; if (typeof value === 'number') return 'number'; return 'text'; }
function renderTaskParamControls(taskId) {
  const params = taskPreset(taskId);
  return Object.entries(params).map(([key, value]) => {
    const type = taskFieldType(value);
    const checked = type === 'checkbox' && value ? 'checked' : '';
    const val = type === 'checkbox' ? '' : `value="${escapeHtml(value)}"`;
    return `<label class="task-param"><span>${escapeHtml(key)}</span><input data-task-id="${escapeHtml(taskId)}" data-param-key="${escapeHtml(key)}" type="${type}" ${val} ${checked}></label>`;
  }).join('');
}
function coerceParamValue(raw, inputType) {
  if (inputType === 'checkbox') return raw === true;
  if (inputType === 'number') { const n = Number(raw); return Number.isFinite(n) ? n : raw; }
  const text = String(raw ?? '').trim();
  if (text.toLowerCase() === 'true') return true;
  if (text.toLowerCase() === 'false') return false;
  if (/^[A-Z0-9]{6}\.S[HZ](,[A-Z0-9]{6}\.S[HZ])*$/.test(text)) return text.split(',').map((item) => item.trim());
  return text;
}
function hardenTaskParams(params = {}) {
  const hardened = {...params};
  hardened.allow_order_submit = false;
  hardened.allow_order_cancel = false;
  hardened.order_submit_enabled = false;
  hardened.order_cancel_enabled = false;
  hardened.real_order_submitted = false;
  if (!('dry_run' in hardened)) hardened.dry_run = true;
  if (!('read_only' in hardened)) hardened.read_only = true;
  return hardened;
}
function collectTaskParams(taskId) {
  const params = {};
  document.querySelectorAll(`[data-task-id="${CSS.escape(taskId)}"][data-param-key]`).forEach((input) => {
    const key = input.dataset.paramKey;
    const value = input.type === 'checkbox' ? input.checked : input.value;
    params[key] = coerceParamValue(value, input.type);
  });
  if (!('limit' in params)) params.limit = 5;
  return hardenTaskParams(params);
}
function workflowParams(taskId) {
  const preset = taskPreset(taskId);
  const params = {...preset};
  if (typeof params.symbols === 'string') params.symbols = params.symbols.split(',').map((item) => item.trim()).filter(Boolean);
  return hardenTaskParams(params);
}
function orderedColumns(rows) {
  const preferred = ['symbol', 'period', 'time', 'index', 'preview_id', 'approval_id', 'approval_status', 'intent_id', 'order_id', 'paper_order_id', 'side', 'quantity', 'target_weight', 'decision', 'status', 'risk_decision', 'paper_status', 'shadow_status', 'fill_status', 'open', 'high', 'low', 'close', 'volume', 'amount', 'source', 'real_market_data', 'sandbox_fallback', 'can_submit_order'];
  const all = [...new Set(rows.flatMap((item) => Object.keys(item)))];
  const ordered = preferred.filter((key) => all.includes(key)).concat(all.filter((key) => !preferred.includes(key)));
  return ordered.slice(0, 14);
}
function renderRowsTable(rows, title = '表格数据') {
  if (!Array.isArray(rows) || !rows.length) return '<p class="empty">暂无可展示的表格数据。</p>';
  const objects = rows.filter((row) => row && typeof row === 'object' && !Array.isArray(row));
  if (!objects.length) return renderList({rows});
  const cols = orderedColumns(objects);
  return `<div class="task-market-table"><h4>${escapeHtml(title)}</h4><table><thead><tr>${cols.map((col) => `<th>${escapeHtml(humanKey(col))}</th>`).join('')}</tr></thead><tbody>${objects.slice(-20).map((row) => `<tr>${cols.map((col) => `<td>${formatCell(row[col])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function sortTasksForWorkflow(tasks) {
  const priority = new Map(TASK_PRIORITY.map((id, idx) => [id, idx]));
  return [...tasks].sort((a, b) => {
    const ai = priority.has(a.task_id) ? priority.get(a.task_id) : 1000;
    const bi = priority.has(b.task_id) ? priority.get(b.task_id) : 1000;
    if (ai !== bi) return ai - bi;
    return String(a.category || '').localeCompare(String(b.category || '')) || String(a.task_id).localeCompare(String(b.task_id));
  });
}
async function renderUpdatedArtifacts(taskId) {
  if (taskId === 'xtdata_live_readonly_smoke' || taskId === 'market_snapshot_readonly') {
    const market = await apiGet('/datahub/market/latest');
    const payload = market.market || market;
    const rows = payload.latest || payload.rows || [];
    return `<section class="task-artifact-preview"><h4>已写入 Data Hub 最新行情</h4>${renderMetricCards(payload)}${renderRowsTable(rows, 'Data Hub / market latest')}</section>`;
  }
  if (taskId === 'etf_rotation_candidates' || taskId === 'factor_scan' || taskId === 'factor_research_dry_run') {
    const data = await apiGet('/research/candidates/latest');
    return `<section class="task-artifact-preview"><h4>已写入 Research 候选池</h4>${renderList(data.candidates || data)}</section>`;
  }
  if (taskId === 'strategy_dry_run_signals' || taskId === 'factor_strategy_dry_run') {
    const intents = await apiGet('/strategy/trade-intents/latest');
    return `<section class="task-artifact-preview"><h4>已写入 TradeIntent dry-run</h4>${renderList(intents.trade_intents || intents)}</section>`;
  }
  if (taskId === 'risk_gate_dry_run') {
    const decisions = await apiGet('/risk/decisions/latest');
    return `<section class="task-artifact-preview"><h4>已写入 Risk Gate 决策</h4>${renderList(decisions.decisions || decisions)}</section>`;
  }
  if (taskId === 'paper_trading_dry_run') {
    const status = await apiGet('/paper-trading/status');
    const orders = await apiGet('/paper-trading/orders/latest');
    const positions = await apiGet('/paper-trading/positions/latest');
    const pnl = await apiGet('/paper-trading/pnl/latest');
    const orderPayload = orders.orders || orders;
    const positionPayload = positions.positions || positions;
    return `<section class="task-artifact-preview"><h4>已写入 Paper / Shadow 产物</h4>${renderMetricCards(status.report || status)}${renderRowsTable(orderPayload.orders || [], 'Paper Orders')}${renderRowsTable(positionPayload.positions || [], 'Shadow Positions')}${renderList(pnl.pnl || pnl)}</section>`;
  }
  if (taskId === 'human_approval_review_dry_run') {
    const status = await apiGet('/approval/status');
    const requests = await apiGet('/approval/requests/latest');
    return `<section class="task-artifact-preview"><h4>已写入 Human Approval 人工复核卡</h4>${renderMetricCards(status.approval || status)}${renderRowsTable(requests.requests || [], 'Human Approval Requests')}</section>`;
  }
  if (taskId === 'order_preview_dry_run') {
    const status = await apiGet('/portfolio/status');
    const preview = await apiGet('/portfolio/order-preview/latest');
    const budget = await apiGet('/portfolio/budget/latest');
    return `<section class="task-artifact-preview"><h4>已写入 Portfolio 订单预览</h4>${renderMetricCards(status)}${renderRowsTable(preview.previews || [], 'Order Preview')}${renderMetricCards(budget.budget || budget)}</section>`;
  }
  return '';
}
renderTaskPanel = async function() {
  try {
    const catalog = await apiGet('/tasks/catalog');
    const tasks = sortTasksForWorkflow(catalog.tasks || []);
    if (!tasks.length) return '<p class="empty">暂无可执行任务。</p>';
    return `<section class="card">
      <h3>白名单任务</h3>
      <p class="hint">点击任务卡片后可先检查参数，再运行。推荐顺序：xtdata 只读行情 smoke → 多因子扫描 → 策略 dry-run 信号 → Risk Gate dry-run → Paper Trading / Shadow Trading dry-run → Human Approval 人工复核 dry-run → 订单预览 dry-run。Account Readonly 默认只读查询资产/持仓；下单和撤单参数会被前端与后端同时固定为 false。</p>
      <div class="task-grid">${tasks.map((task) => `
        <article class="task-card task-card-panel">
          <button class="task-title" onclick="selectTask('${escapeHtml(task.task_id)}')">
            <strong>${escapeHtml(task.title_zh || task.task_id)}</strong>
            <span>${escapeHtml(task.category || 'TASK')}</span>
            <small>${escapeHtml(task.description_zh || '只读 / dry-run 任务')}</small>
          </button>
          <div id="params_${escapeHtml(task.task_id)}" class="task-param-panel" hidden>
            <div class="task-param-grid">${renderTaskParamControls(task.task_id)}</div>
            <button class="task-run-button" onclick="runTask('${escapeHtml(task.task_id)}')">运行该任务</button>
          </div>
        </article>`).join('')}</div>
      <div id="taskResult" class="task-result empty">选择任务并确认参数后，会在这里显示运行状态、日志摘要和已写入的统一控制台产物。</div>
    </section>`;
  } catch (error) {
    return `<p class="empty">任务目录暂不可用：${escapeHtml(error.message)}</p>`;
  }
};
function selectTask(taskId) {
  document.querySelectorAll('.task-param-panel').forEach((panel) => { panel.hidden = true; });
  const panel = document.getElementById(`params_${taskId}`);
  if (panel) panel.hidden = false;
  const box = document.getElementById('taskResult');
  if (box) { box.className = 'task-result empty'; box.textContent = `已选择任务：${taskId}，请确认参数后运行。`; }
}
runTask = async function(taskId) {
  const box = $('taskResult');
  if (!box) return;
  const params = collectTaskParams(taskId);
  box.className = 'task-result';
  box.innerHTML = '任务运行中...';
  try {
    const res = await apiPost('/tasks/run', {task_id: taskId, params});
    const task = res.task || {};
    const artifactPreview = await renderUpdatedArtifacts(taskId);
    box.innerHTML = `<h4>${escapeHtml(task.task_name || taskId)}</h4>
      <p>${badge(task.status || 'SUCCESS')} ${badge('dry-run')} ${badge('未下单')} ${badge('产物已更新')}</p>
      <p class="hint">运行参数：${escapeHtml(JSON.stringify(task.params || params))}</p>
      <ul class="plain-list">${(task.logs || []).slice(-8).map((line) => `<li>${escapeHtml(line)}</li>`).join('')}</ul>
      ${renderMetricCards(task.output || {})}
      ${artifactPreview || renderList(task.output || {})}`;
  } catch (error) {
    box.className = 'task-result empty';
    box.textContent = `任务失败：${error.message}`;
  }
};
function workflowStepRow(step, state = 'WAIT', detail = '') {
  return `<div class="workflow-step ${state.toLowerCase()}" id="wf_${escapeHtml(step.taskId)}"><strong>${escapeHtml(step.title)}</strong><span>${badge(state === 'SUCCESS' ? 'ok' : state === 'FAILED' ? 'warn' : 'neutral', state)}</span><small>${escapeHtml(detail || step.reads || '')}</small></div>`;
}
function workflowGuardFind(obj, path = '') {
  const hits = [];
  if (!obj || typeof obj !== 'object') return hits;
  for (const [key, value] of Object.entries(obj)) {
    const next = path ? `${path}.${key}` : key;
    if (UNSAFE_TRUE_KEYS.has(key) && value === true) hits.push(next);
    if (value && typeof value === 'object') hits.push(...workflowGuardFind(value, next));
  }
  return hits;
}
async function workflowSnapshotHtml() {
  const cards = [];
  for (const [title, endpoint] of WORKFLOW_SNAPSHOT_ENDPOINTS) {
    try {
      const data = await apiGet(endpoint);
      const status = data.status || data.feature_status || data.business_status || 'READY';
      cards.push(`<article class="workflow-snapshot-card"><div class="endpoint-head"><h4>${escapeHtml(title)}</h4>${badge(status)}</div>${renderMetricCards(data)}${renderList(data)}</article>`);
    } catch (error) {
      cards.push(`<article class="workflow-snapshot-card pending"><div class="endpoint-head"><h4>${escapeHtml(title)}</h4>${badge('warn', 'DATA_MISSING')}</div><p class="empty">${escapeHtml(endpoint)} 暂不可读：${escapeHtml(error.message)}</p></article>`);
    }
  }
  return `<div class="workflow-snapshot-grid">${cards.join('')}</div>`;
}
async function renderWorkflowPanel() {
  return `<section class="card workflow-panel">
    <div class="endpoint-head">
      <div>
        <h3>灰度前 dry-run 一键观察链路</h3>
        <p class="hint">顺序执行 7 个只读 / dry-run 任务，并实时检查安全旗标。该按钮不会打开实盘、不会下单、不会撤单。</p>
      </div>
      ${badge('ok', 'can_submit_order=false')}
    </div>
    <div class="workflow-actions">
      <button class="task-run-button workflow-run-button" onclick="runDryRunWorkflow()">一键运行灰度前 dry-run 链路</button>
      <button class="refresh" onclick="refreshWorkflowSnapshot()">只刷新当前产物快照</button>
    </div>
    <div id="workflowSteps" class="workflow-steps">${DRYRUN_WORKFLOW.map((step) => workflowStepRow(step)).join('')}</div>
    <div id="workflowResult" class="task-result empty">点击一键运行后，将显示每一步结果、日志摘要和最终安全结论。</div>
    <div id="workflowSnapshot" class="workflow-snapshot empty">产物快照将在运行后显示。</div>
  </section>`;
}
async function refreshWorkflowSnapshot() {
  const snapshot = $('workflowSnapshot');
  if (!snapshot) return;
  snapshot.className = 'workflow-snapshot';
  snapshot.innerHTML = '正在读取统一控制台产物...';
  snapshot.innerHTML = await workflowSnapshotHtml();
}
function setWorkflowStep(step, state, detail = '') {
  const node = document.getElementById(`wf_${step.taskId}`);
  if (node) node.outerHTML = workflowStepRow(step, state, detail);
}
async function runDryRunWorkflow() {
  const result = $('workflowResult');
  const snapshot = $('workflowSnapshot');
  if (!result) return;
  result.className = 'task-result';
  result.innerHTML = '<h4>灰度前 dry-run 链路运行中...</h4><p class="hint">正在按顺序执行，不允许下单、不允许撤单。</p>';
  if (snapshot) snapshot.innerHTML = '';
  const rows = [];
  const safetyHits = [];
  for (const step of DRYRUN_WORKFLOW) {
    setWorkflowStep(step, 'RUNNING', '正在执行');
    try {
      const params = workflowParams(step.taskId);
      const res = await apiPost('/tasks/run', {task_id: step.taskId, params});
      const task = res.task || {};
      const output = task.output || {};
      const hits = workflowGuardFind({response: res, output});
      safetyHits.push(...hits);
      const taskStatus = task.status || 'SUCCESS';
      const businessStatus = output.status || output.paper_trading_status || output.safety_status || '';
      rows.push({task_id: step.taskId, task_status: taskStatus, business_status: businessStatus, artifact_count: (task.output_artifacts || []).length, unsafe_flags: hits.join(', ')});
      setWorkflowStep(step, taskStatus === 'SUCCESS' && hits.length === 0 ? 'SUCCESS' : 'FAILED', hits.length ? `unsafe: ${hits.join(', ')}` : (businessStatus || 'OK'));
      result.innerHTML = `<h4>灰度前 dry-run 链路运行中...</h4>${renderRowsTable(rows, 'Workflow live results')}<p class="hint">最近完成：${escapeHtml(step.taskId)}</p>`;
      if (taskStatus !== 'SUCCESS' || hits.length) throw new Error(`${step.taskId} safety check failed`);
    } catch (error) {
      setWorkflowStep(step, 'FAILED', error.message);
      result.className = 'task-result empty';
      result.innerHTML = `<h4>链路中断</h4><p>${escapeHtml(step.taskId)} 失败：${escapeHtml(error.message)}</p>${renderRowsTable(rows, 'Workflow partial results')}`;
      await refreshWorkflowSnapshot();
      return;
    }
  }
  let previewStatus = {};
  try { previewStatus = await apiGet('/portfolio/status'); } catch (_) { previewStatus = {}; }
  const canSubmit = previewStatus.can_submit_order === true;
  if (canSubmit) safetyHits.push('portfolio.status.can_submit_order');
  result.className = canSubmit || safetyHits.length ? 'task-result empty' : 'task-result';
  result.innerHTML = `<h4>${canSubmit || safetyHits.length ? '安全检查未通过' : '灰度前 dry-run 链路通过'}</h4>
    <p>${badge(!canSubmit && !safetyHits.length, !canSubmit && !safetyHits.length ? 'PASS：can_submit_order=false' : 'BLOCKED')}</p>
    ${renderRowsTable(rows, 'Workflow final results')}
    <p class="hint">最终结论：实盘关闭、未下单、未自动审批；该链路只更新统一控制台产物。</p>`;
  await refreshWorkflowSnapshot();
}
