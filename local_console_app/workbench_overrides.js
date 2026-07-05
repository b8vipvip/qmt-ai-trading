(function(){
  const labels = {ready:'已接入', partial:'部分接入', pending:'待接入'};
  const boards = {
    overview: [
      ['日常 dry-run 操作链路','ready','在总览页一键顺序运行行情、研究、策略、风控、Paper、人工复核和订单预览。'],
      ['安全状态面板','ready','实时检查 can_submit_order、order_submit_enabled、real_order_submitted 等危险旗标。'],
      ['任务历史 / 日志中心','ready','每次任务运行后可在日志中心查看状态、耗时、产物和最近日志。'],
      ['实盘前安全审计','pending','后续接入 go/no-go 审计报告。'],
      ['小资金灰度实盘','pending','必须在安全审计和人工确认后再进入。']
    ],
    datahub: [
      ['QMT 本地行情','ready','xtdata 只读行情和最新行情表已接入。'],
      ['统一标的池','ready','datahub_symbols 已接入。'],
      ['外部数据源','pending','AkShare / Tushare / BaoStock 待后端适配。'],
      ['指数 / ETF / 行业 / 财务 / 新闻','pending','后续接入统一 Data Hub。']
    ],
    research: [
      ['基础多因子扫描','ready','factor_scan 已写入候选池。'],
      ['ETF 研究评分','ready','候选池与评分可展示。'],
      ['Alpha158 / Alpha360 / Alpha101','pending','标准因子库待接入。'],
      ['LightGBM / Lasso / MLP','pending','模型训练与评分待接入。']
    ],
    agent: [
      ['技术面 Agent','partial','可消费行情与因子结果。'],
      ['基本面 Agent','pending','依赖财务与行业数据。'],
      ['情绪 / 新闻 Agent','pending','依赖新闻数据。'],
      ['风险 / 组合 Agent','partial','可读取已有审查和组合预览产物。']
    ],
    strategy: [
      ['ETF 轮动','ready','候选和信号链路已接入。'],
      ['多因子选股','partial','候选池到信号可联动。'],
      ['buy / sell / hold 信号','ready','结构化信号可展示。'],
      ['参数与版本管理','pending','后端待开发，当前只显示待接入状态。']
    ],
    history: [
      ['当前进程任务历史','ready','记录本次 API 进程内执行过的任务。'],
      ['任务日志查看','ready','可按 run_id 查看最近 50 条日志。'],
      ['产物路径追踪','ready','可看到任务写入的统一控制台产物路径。'],
      ['跨进程持久化历史','pending','后续接入 sqlite / duckdb 后可保留重启前历史。']
    ]
  };
  const operationGroups = {
    overview: {title:'日常操作中心', hint:'这里是日常使用入口：先刷新行情，再跑研究、策略、风控、Paper、人工复核和组合预览。所有按钮都会强制 dry-run / read-only / 禁止下单。', actions:[
      ['xtdata_live_readonly_smoke','刷新只读行情','写入 Data Hub 最新行情'],
      ['factor_scan','运行多因子扫描','生成 Research 候选池'],
      ['strategy_dry_run_signals','生成策略信号','输出 TradeIntent dry-run'],
      ['risk_gate_dry_run','执行风控审查','生成 RiskDecision'],
      ['paper_trading_dry_run','运行 Paper / Shadow','生成模拟订单和影子持仓'],
      ['human_approval_review_dry_run','生成人工复核卡','只读审批材料'],
      ['order_preview_dry_run','生成组合订单预览','只预览，不发单'],
      ['account_readonly_dry_run','读取账户 / 持仓','只读、脱敏、禁止交易']
    ]},
    market: {title:'行情操作', hint:'只读取 xtdata / Data Hub 行情，不连接交易接口。', actions:[['xtdata_live_readonly_smoke','刷新 xtdata 行情','更新最新行情表'],['market_snapshot_readonly','读取行情快照','检查 OHLCV 样本']]},
    datahub: {title:'Data Hub 操作', hint:'统一刷新行情、标的池和缓存状态，策略与 Agent 后续只从这里取数。', actions:[['xtdata_live_readonly_smoke','刷新 QMT 本地行情','写入 Data Hub'],['data_cache_check','检查本地缓存质量','查看缺口和完整性'],['market_snapshot_readonly','读取行情快照','展示最新数据']]},
    research: {title:'研究操作', hint:'生成候选池和研究评分，不产生真实订单。', actions:[['factor_scan','多因子扫描','生成候选池'],['research_score_etf','ETF 研究评分','输出 score/rank/reasons'],['model_lab_evaluate','模型实验评估','dry-run 指标摘要']]},
    candidates: {title:'候选池操作', hint:'刷新候选池并检查风险提示。', actions:[['factor_scan','重新生成候选池','覆盖 Research 候选产物'],['research_score_etf','重新评分','更新候选排名']]},
    strategy: {title:'策略操作', hint:'把候选池转换为结构化信号和 TradeIntent，仍然必须进入 Risk Gate。', actions:[['etf_rotation_candidates','ETF 轮动候选','生成候选，不下单'],['strategy_dry_run_signals','策略 dry-run 信号','输出 buy/sell/hold'],['factor_strategy_dry_run','因子策略联调','候选池进入 TradeIntent']]},
    intent: {title:'TradeIntent 操作', hint:'重新生成策略意图，仅 dry-run，不允许提交订单。', actions:[['strategy_dry_run_signals','重新生成 TradeIntent','更新策略意图'],['factor_strategy_dry_run','候选池联调 TradeIntent','进入风控前产物']]},
    risk: {title:'风控操作', hint:'读取 TradeIntent 后生成风控决策，禁止绕过人工审批。', actions:[['risk_gate_dry_run','Risk Gate dry-run','输出 PASS/BLOCKED'],['live_readiness_blockers_review','阻断项复核','列出实盘前阻断项']]},
    paper: {title:'Paper / Shadow 操作', hint:'只消费 dry-run 风控结果，生成模拟订单、影子持仓和 PnL，不接 xttrader。', actions:[['paper_trading_dry_run','运行 Paper / Shadow','更新模拟订单'],['shadow_replay_backtest','Shadow Replay 回测','回放式复盘'],['backtest_report','生成回测报告','输出回测摘要']]},
    approval: {title:'人工复核操作', hint:'生成只读人工审批卡；控制台不会自动批准。', actions:[['human_approval_review_dry_run','生成人工复核卡','读取 RiskDecision 与 PaperOrder'],['live_readiness_blockers_review','复核阻断项','确认不可直接实盘']]},
    account: {title:'账户只读操作', hint:'读取资产和持仓需要你本地确认；结果脱敏展示，仍禁止下单和撤单。', actions:[['account_readonly_dry_run','读取资产 / 持仓','只读、脱敏、禁止交易']]},
    monitoring: {title:'监控操作', hint:'生成异常监控、告警和熔断摘要；当前不发送真实通知。', actions:[['monitoring_alert_dry_run','监控告警 dry-run','生成告警看板']]},
    backtest: {title:'回测操作', hint:'运行回放式回测和分析报告，不触达真实交易。', actions:[['shadow_replay_backtest','Shadow Replay 回测','回放式复盘'],['backtest_dashboard_dry_run','回测分析看板','生成对比看板'],['backtest_report','生成回测报告','输出摘要']]},
    portfolio: {title:'组合预览操作', hint:'读取账户只读、行情、TradeIntent 和 RiskDecision，只计算订单预览与资金占用。', actions:[['order_preview_dry_run','生成订单预览','只预览，不发单'],['account_readonly_dry_run','刷新账户只读','更新资金/持仓'],['risk_gate_dry_run','复查风控结果','更新 RiskDecision']]},
    history: {title:'历史操作', hint:'查看本次 API 进程内任务执行历史、日志和产物路径。', actions:[['xtdata_live_readonly_smoke','跑一次行情 smoke','生成一条历史记录'],['factor_scan','跑一次因子扫描','生成一条历史记录'],['risk_gate_dry_run','跑一次风控审查','生成一条历史记录']]}
  };

  window.__workbenchActionResults = window.__workbenchActionResults || {};

  function patch(id,name,lead){const m=modules.find(x=>x.id===id);if(m){if(name)m.name=name;if(lead)m.lead=lead;}}
  function ensureModule(module, afterId){
    if(modules.find(x=>x.id===module.id)) return;
    const index = modules.findIndex(x=>x.id===afterId);
    modules.splice(index >= 0 ? index + 1 : modules.length, 0, module);
  }

  patch('overview','总览 / 日常操作台','一键运行 dry-run 链路，按模块启动任务，查看行情、研究、策略、风控、Paper、审批、账户只读和组合预览。');
  patch('datahub','Data Hub 数据源中心','统一管理行情、标的池、缓存和后续外部数据源；策略与 Agent 只能从 Data Hub 取数。');
  patch('agent','Agent 投研工作台','运行和查看 Agent 投研结果；只输出结构化建议，不允许跳过风控或直接下单。');
  patch('strategy','Strategy Engine 策略工作台','运行和查看策略信号、TradeIntent 与候选结果；策略输出必须进入 Risk Gate。');
  patch('tasks','任务执行 / 操作入口','选择白名单任务，确认参数后运行；所有任务保持只读 / dry-run / 不下单。');
  patch('safety','Safety / 安全边界','集中查看实盘、下单、撤单、自动批准和账户脱敏状态。');
  ensureModule({id:'history',name:'任务历史 / 日志中心',lead:'查看每次任务执行时间、状态、参数、产物路径和最近日志；当前为本次 API 进程内历史。',eps:['/tasks/history']}, 'tasks');
  const overview = modules.find(x=>x.id==='overview');
  if(overview){overview.workflowPanel=true;}

  function boardHtml(id){
    const rows=boards[id];
    if(!rows)return'';
    return `<section class="card workbench-card"><div class="endpoint-head"><div><h3>模块能力地图</h3><p class="hint">已接入能力展示真实业务产物；未接入能力明确标注，不伪造结果。</p></div>${badge('ok','工作台')}</div><div class="capability-grid">${rows.map(([t,s,d])=>`<div class="capability-item ${s}"><div class="capability-title">${escapeHtml(t)} ${badge(s==='pending'?'warn':'ok',labels[s])}</div><p>${escapeHtml(d)}</p></div>`).join('')}</div></section>`;
  }
  function heroHtml(module,state){
    return `<section class="card hero ${state.cls==='warn'?'pending':''}"><div class="module-title"><div><h2>${escapeHtml(module.name)}</h2><p>${escapeHtml(module.lead)}</p><p class="hint">这是你的本地量化系统工作台：页面直接调用后端业务接口；按钮会触发白名单任务并刷新统一产物，不再把验收记录作为主内容。</p></div>${badge(state.cls==='ok'?'ok':'warn',state.label)}</div><div class="module-safety">${safetyBar({})}</div>${queryForm(module)}</section>`;
  }
  function defaultOperationHtml(){return '点击上方操作后，这里会显示任务运行结果、日志和更新后的业务产物。';}
  function operationBoxHtml(id){
    const saved=window.__workbenchActionResults[id];
    if(!saved)return `<div id="operationResult_${escapeHtml(id)}" class="task-result empty">${defaultOperationHtml()}</div>`;
    return `<div id="operationResult_${escapeHtml(id)}" class="${escapeHtml(saved.className||'task-result')}">${saved.html}</div>`;
  }
  function actionPanelHtml(id){
    const group=operationGroups[id];
    if(!group)return'';
    return `<section class="card operation-panel"><div class="endpoint-head"><div><h3>${escapeHtml(group.title)}</h3><p class="hint">${escapeHtml(group.hint)}</p></div>${badge('ok','操作入口')}</div><div class="operation-grid">${group.actions.map(([taskId,title,desc])=>`<button class="operation-action" onclick="runWorkbenchAction('${escapeHtml(taskId)}','${escapeHtml(id)}')"><strong>${escapeHtml(title)}</strong><small>${escapeHtml(taskId)}</small><span>${escapeHtml(desc)}</span></button>`).join('')}</div>${operationBoxHtml(id)}</section>`;
  }
  function endpointGridHtml(results){return `<section class="grid">${results.map(item=>renderEndpoint(item.endpoint,item.data)).join('')}</section>`;}
  function diagnosticsHtml(results){return `<details class="card technical-diagnostics"><summary>系统接口与诊断结果（默认折叠）</summary><p class="hint">这里保留接口连通性和原始产物视图，日常操作优先看上方操作中心和业务模块。</p>${endpointGridHtml(results)}</details>`;}
  function setOperationResult(moduleId,className,html){
    window.__workbenchActionResults[moduleId]={className,html};
    const box=document.getElementById(`operationResult_${moduleId}`)||document.getElementById('taskResult');
    if(box){box.className=className;box.innerHTML=html;}
  }

  function historyStatus(run){return run.status || 'UNKNOWN';}
  function shortRunId(runId){return String(runId||'').slice(0,8);}
  function historyRowsHtml(runs){
    if(!Array.isArray(runs)||!runs.length)return '<p class="empty">暂无任务历史。先在总览页或任务入口运行一个 dry-run 任务。</p>';
    return `<div class="task-history-table"><table><thead><tr><th>时间</th><th>任务</th><th>状态</th><th>分类</th><th>产物数</th><th>run id</th><th>日志</th></tr></thead><tbody>${runs.slice(0,50).map((run)=>`<tr><td>${escapeHtml(run.finished_at||run.started_at||'')}</td><td><strong>${escapeHtml(run.task_name||run.task_id)}</strong><br><small>${escapeHtml(run.task_id||'')}</small></td><td>${badge(historyStatus(run))}</td><td>${escapeHtml(run.category||'')}</td><td>${escapeHtml((run.output_artifacts||[]).length)}</td><td><code>${escapeHtml(shortRunId(run.run_id))}</code></td><td><button class="mini-button" onclick="viewTaskLogs('${escapeHtml(run.run_id)}')">查看日志</button></td></tr>`).join('')}</tbody></table></div>`;
  }
  function historyArtifactHtml(run){
    const artifacts = run && Array.isArray(run.output_artifacts) ? run.output_artifacts : [];
    if(!artifacts.length)return '<p class="empty">该任务暂无产物路径。</p>';
    return `<ul class="plain-list artifact-list">${artifacts.slice(0,20).map((item)=>`<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
  }
  function historyPanelHtml(data){
    const runs = data.runs || data.tasks || [];
    const latest = runs[0] || {};
    return `<section class="card task-history-panel">
      <div class="endpoint-head"><div><h3>任务历史 / 日志中心</h3><p class="hint">记录当前 API 进程内的任务运行历史。重启 API 后历史会清空；后续可接入 sqlite / duckdb 做持久化。</p></div>${badge(data.status||'READY')}</div>
      <div class="history-toolbar"><button class="refresh" onclick="refreshTaskHistory()">刷新历史</button>${latest.run_id?`<button class="refresh" onclick="viewTaskLogs('${escapeHtml(latest.run_id)}')">查看最新日志</button>`:''}</div>
      <div class="metrics history-metrics">
        <div class="metric"><span>当前显示</span><strong>${escapeHtml(data.run_count||runs.length||0)}</strong></div>
        <div class="metric"><span>总运行数</span><strong>${escapeHtml(data.total_run_count||runs.length||0)}</strong></div>
        <div class="metric"><span>成功</span><strong>${escapeHtml(data.success_count||0)}</strong></div>
        <div class="metric"><span>失败</span><strong>${escapeHtml(data.failed_count||0)}</strong></div>
        <div class="metric"><span>最新任务</span><strong>${escapeHtml(data.latest_task_id||latest.task_id||'无')}</strong></div>
      </div>
      <div id="taskHistoryResult">${historyRowsHtml(runs)}</div>
      <div id="taskLogViewer" class="task-log-viewer empty">点击“查看日志”后，这里显示该任务的最近日志和产物路径。</div>
    </section>`;
  }
  window.refreshTaskHistory = async function(){
    const box=document.getElementById('taskHistoryResult');
    if(box)box.innerHTML='正在刷新任务历史...';
    try{
      const data=await apiGet('/tasks/history?limit=50');
      if(box)box.innerHTML=historyRowsHtml(data.runs||[]);
      const viewer=document.getElementById('taskLogViewer');
      if(viewer&&!((data.runs||[]).length))viewer.textContent='暂无任务历史。';
    }catch(error){
      if(box)box.innerHTML=`<p class="empty">刷新失败：${escapeHtml(error.message)}</p>`;
    }
  };
  window.viewTaskLogs = async function(runId){
    const viewer=document.getElementById('taskLogViewer');
    if(!viewer)return;
    viewer.className='task-log-viewer';
    viewer.innerHTML='正在读取日志...';
    try{
      const [logsData, runData]=await Promise.all([apiGet(`/tasks/${encodeURIComponent(runId)}/logs`), apiGet(`/tasks/${encodeURIComponent(runId)}`)]);
      const run=runData.task||{};
      viewer.innerHTML=`<h4>${escapeHtml(run.task_name||run.task_id||runId)}</h4><p>${badge(run.status||'READY')} <code>${escapeHtml(run.run_id||runId)}</code></p><ul class="plain-list">${(logsData.logs||[]).map((line)=>`<li>${escapeHtml(line)}</li>`).join('')}</ul><h4>产物路径</h4>${historyArtifactHtml(run)}`;
    }catch(error){
      viewer.className='task-log-viewer empty';
      viewer.textContent=`读取日志失败：${error.message}`;
    }
  };

  window.runWorkbenchAction = async function(taskId,moduleId){
    const loading=`<h4>${escapeHtml(taskId)} 运行中...</h4><p class="hint">已强制 dry-run/read-only，禁止下单和撤单。</p>`;
    setOperationResult(moduleId,'task-result',loading);
    try{
      const params=typeof workflowParams==='function'?workflowParams(taskId):{limit:5,dry_run:true,read_only:true,allow_order_submit:false,allow_order_cancel:false};
      const res=await apiPost('/tasks/run',{task_id:taskId,params});
      const task=res.task||{};
      const hits=typeof workflowGuardFind==='function'?workflowGuardFind({response:res,output:task.output||{}}):[];
      const artifactPreview=typeof renderUpdatedArtifacts==='function'?await renderUpdatedArtifacts(taskId):'';
      const ok=(task.status||'SUCCESS')==='SUCCESS'&&!hits.length;
      const historyLink=task.run_id?`<p class="hint">run_id：<code>${escapeHtml(task.run_id)}</code>，可在“任务历史 / 日志中心”查看完整记录。</p>`:'';
      const html=`<h4>${escapeHtml(task.task_name||taskId)}</h4><p>${badge(ok,'运行完成')} ${badge('dry-run')} ${badge('未下单')} ${hits.length?badge('warn','发现危险旗标'):badge('ok','安全旗标通过')} ${badge('ok','产物已刷新')}</p>${historyLink}<p class="hint">运行参数：${escapeHtml(JSON.stringify(task.params||params))}</p><ul class="plain-list">${(task.logs||[]).slice(-8).map((line)=>`<li>${escapeHtml(line)}</li>`).join('')}</ul>${renderMetricCards(task.output||{})}${artifactPreview||renderList(task.output||{})}`;
      setOperationResult(moduleId,ok?'task-result':'task-result empty',html);
      if(moduleId==='history') await refreshTaskHistory();
      setTimeout(()=>show(moduleId),700);
    }catch(error){
      setOperationResult(moduleId,'task-result empty',`任务失败：${escapeHtml(error.message)}`);
    }
  };

  show = async function(id){
    const module=modules.find(item=>item.id===id)||modules[0];
    document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.id===module.id||b.id===`nav_${module.id}`));
    const app=$('app');
    app.innerHTML='<section class="card">加载中...</section>';
    if(!module.eps?.length&&module.pendingItems){app.innerHTML=renderStatic(module);return;}
    const query=endpointQuery(module);
    const results=await loadModule(module,query);
    const state=moduleState(results);
    let html=heroHtml(module,state)+actionPanelHtml(module.id)+boardHtml(module.id);
    if(module.id==='history'){
      html += historyPanelHtml(results[0]?.data||{});
      app.innerHTML=html;
      $('safety').innerHTML=safetyBar(results[0]?.data||{});
      return;
    }
    if(module.workflowPanel&&typeof renderWorkflowPanel==='function') html+=await renderWorkflowPanel();
    if(module.taskPanel) html+=await renderTaskPanel();
    else if(module.id==='overview') html+=diagnosticsHtml(results);
    else html+=endpointGridHtml(results);
    app.innerHTML=html;
    const firstPayload=results.find(item=>item.data&&!item.error)?.data||{};
    $('safety').innerHTML=safetyBar(firstPayload);
  };

  buildNav();
  show('overview');
})();
