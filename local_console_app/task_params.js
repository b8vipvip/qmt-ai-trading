const TASK_PARAM_PRESETS = {
  market_snapshot_readonly: {
    symbol: '510300.SH',
    limit: 5,
  },
  xtdata_live_readonly_smoke: {
    enable_xtdata: true,
    allow_import_xtdata: true,
    allow_connect_miniqmt: true,
    allow_real_market_data: true,
    symbols: '510300.SH,159915.SZ,510500.SH',
    period: '1d',
    limit: 20,
    allow_xttrader: false,
    allow_account_query: false,
    allow_order_submit: false,
  },
  etf_rotation_candidates: {
    symbol: '510300.SH',
    limit: 5,
  },
  factor_strategy_dry_run: {
    symbol: '510300.SH',
    limit: 5,
    max_positions: 3,
  },
  strategy_dry_run_signals: {
    symbol: '510300.SH',
    limit: 5,
  },
  risk_gate_dry_run: {
    limit: 5,
  },
  paper_trading_dry_run: {
    limit: 5,
  },
  monitoring_alert_dry_run: {
    limit: 5,
  },
  account_readonly_dry_run: {
    enable_account_readonly: false,
    manual_confirmed: false,
    allow_import_xttrader: false,
    allow_connect_trade_session: false,
    allow_account_query: false,
    allow_position_query: false,
    allow_order_submit: false,
    allow_order_cancel: false,
    dry_run: true,
    read_only: true,
  },
};

function taskPreset(taskId) {
  return TASK_PARAM_PRESETS[taskId] || {limit: 5};
}

function taskFieldType(value) {
  if (typeof value === 'boolean') return 'checkbox';
  if (typeof value === 'number') return 'number';
  return 'text';
}

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
  if (inputType === 'number') {
    const n = Number(raw);
    return Number.isFinite(n) ? n : raw;
  }
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

renderTaskPanel = async function() {
  try {
    const catalog = await apiGet('/tasks/catalog');
    const tasks = (catalog.tasks || []).slice(0, 24);
    if (!tasks.length) return '<p class="empty">暂无可执行任务。</p>';
    return `<section class="card">
      <h3>白名单任务</h3>
      <p class="hint">点击任务卡片后可先检查参数，再运行。所有任务仍强制只读 / dry-run；下单和撤单参数会被前端与后端同时固定为 false。</p>
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
      <div id="taskResult" class="task-result empty">选择任务并确认参数后，会在这里显示运行状态和日志摘要。</div>
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
  if (box) {
    box.className = 'task-result empty';
    box.textContent = `已选择任务：${taskId}，请确认参数后运行。`;
  }
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
    box.innerHTML = `<h4>${escapeHtml(task.task_name || taskId)}</h4>
      <p>${badge(task.status || 'SUCCESS')} ${badge('dry-run')} ${badge('未下单')} ${badge('产物已更新')}</p>
      <p class="hint">运行参数：${escapeHtml(JSON.stringify(task.params || params))}</p>
      <ul class="plain-list">${(task.logs || []).slice(-8).map((line) => `<li>${escapeHtml(line)}</li>`).join('')}</ul>
      ${renderMetricCards(task.output || {})}
      ${renderList(task.output || {})}`;
  } catch (error) {
    box.className = 'task-result empty';
    box.textContent = `任务失败：${error.message}`;
  }
};
