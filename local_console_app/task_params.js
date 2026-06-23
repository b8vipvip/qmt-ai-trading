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
  monitoring_alert_dry_run: {limit: 5},
  account_readonly_dry_run: {enable_account_readonly: true, manual_confirmed: true, allow_import_xttrader: true, allow_connect_trade_session: true, allow_account_query: true, allow_position_query: true, account_timeout_seconds: 120, allow_order_submit: false, allow_order_cancel: false, dry_run: true, read_only: true},
};

const TASK_PRIORITY = ['xtdata_live_readonly_smoke', 'factor_scan', 'strategy_dry_run_signals', 'risk_gate_dry_run', 'paper_trading_dry_run', 'human_approval_review_dry_run', 'account_readonly_dry_run'];

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
function collectTaskParams(taskId) {
  const params = {};
  document.querySelectorAll(`[data-task-id="${CSS.escape(taskId)}"][data-param-key]`).forEach((input) => {
    const key = input.dataset.paramKey;
    const value = input.type === 'checkbox' ? input.checked : input.value;
    params[key] = coerceParamValue(value, input.type);
  });
  if (!('limit' in params)) params.limit = 5;
  params.allow_order_submit = false;
  params.allow_order_cancel = false;
  if (!('dry_run' in params)) params.dry_run = true;
  if (!('read_only' in params)) params.read_only = true;
  return params;
}
function orderedColumns(rows) {
  const preferred = ['symbol', 'period', 'time', 'index', 'approval_id', 'approval_status', 'intent_id', 'order_id', 'paper_order_id', 'side', 'quantity', 'target_weight', 'decision', 'status', 'risk_decision', 'paper_status', 'shadow_status', 'fill_status', 'open', 'high', 'low', 'close', 'volume', 'amount', 'source', 'real_market_data', 'sandbox_fallback'];
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
  return '';
}
renderTaskPanel = async function() {
  try {
    const catalog = await apiGet('/tasks/catalog');
    const tasks = sortTasksForWorkflow(catalog.tasks || []);
    if (!tasks.length) return '<p class="empty">暂无可执行任务。</p>';
    return `<section class="card">
      <h3>白名单任务</h3>
      <p class="hint">点击任务卡片后可先检查参数，再运行。推荐顺序：xtdata 只读行情 smoke → 多因子扫描 → 策略 dry-run 信号 → Risk Gate dry-run → Paper Trading / Shadow Trading dry-run → Human Approval 人工复核 dry-run。Account Readonly 默认只读查询资产/持仓；下单和撤单参数会被前端与后端同时固定为 false。</p>
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
