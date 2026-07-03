(function(){
  const labels={ready:'已接入',partial:'部分接入',pending:'后端待接入'};
  const boards={
    datahub:[['QMT 本地行情','ready','xtdata 只读行情和最新行情表已接入。'],['统一标的池','ready','datahub_symbols 已接入。'],['外部数据源','pending','AkShare / Tushare / BaoStock 待后端适配。'],['指数 / ETF / 行业 / 财务 / 新闻','pending','后续接入统一 Data Hub。']],
    research:[['基础多因子扫描','ready','factor_scan 已写入候选池。'],['ETF 研究评分','ready','候选池与评分可展示。'],['Alpha158 / Alpha360 / Alpha101','pending','标准因子库待接入。'],['LightGBM / Lasso / MLP','pending','模型训练与评分待接入。']],
    agent:[['技术面 Agent','partial','可消费行情与因子结果。'],['基本面 Agent','pending','依赖财务与行业数据。'],['情绪 / 新闻 Agent','pending','依赖新闻数据。'],['风险 / 组合 Agent','partial','可读取已有审查和组合预览产物。']],
    strategy:[['ETF 轮动','ready','候选和信号链路已接入。'],['多因子选股','partial','候选池到信号可联动。'],['buy / sell / hold 信号','ready','结构化信号可展示。'],['参数与版本管理','pending','后端待开发，当前不伪造。']]
  };
  function patch(id,name,lead){const m=modules.find(x=>x.id===id);if(m){if(name)m.name=name;if(lead)m.lead=lead;}}
  patch('datahub','Data Hub 数据源中心','统一管理行情、标的池、缓存和后续外部数据源；策略与 Agent 只能从 Data Hub 取数。');
  patch('agent','Agent 投研工作台');
  patch('strategy','Strategy Engine 策略工作台');
  function boardHtml(id){const rows=boards[id];if(!rows)return'';return `<section class="card workbench-card"><div class="endpoint-head"><div><h3>模块能力地图</h3><p class="hint">已完成能力展示真实产物；未完成能力明确标注，不伪造结果。</p></div>${badge('ok','工作台')}</div><div class="capability-grid">${rows.map(([t,s,d])=>`<div class="capability-item ${s}"><div class="capability-title">${escapeHtml(t)} ${badge(s==='pending'?'warn':'ok',labels[s])}</div><p>${escapeHtml(d)}</p></div>`).join('')}</div></section>`;}
  function heroHtml(module,state){return `<section class="card hero ${state.cls==='warn'?'pending':''}"><div class="module-title"><div><h2>${escapeHtml(module.name)}</h2><p>${escapeHtml(module.lead)}</p><p class="hint">当前页面直接读取业务产物；未完成能力会明确标注，不用阶段入口。</p></div>${badge(state.cls==='ok'?'ok':'warn',state.label)}</div><div class="module-safety">${safetyBar({})}</div>${queryForm(module)}</section>`;}
  show=async function(id){const module=modules.find(item=>item.id===id)||modules[0];document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.id===`nav_${module.id}`));const app=$('app');app.innerHTML='<section class="card">加载中...</section>';if(!module.eps?.length&&module.pendingItems){app.innerHTML=renderStatic(module);return;}const query=endpointQuery(module);const results=await loadModule(module,query);const state=moduleState(results);let html=heroHtml(module,state)+boardHtml(module.id);html+=module.taskPanel?await renderTaskPanel():`<section class="grid">${results.map(item=>renderEndpoint(item.endpoint,item.data)).join('')}</section>`;app.innerHTML=html;const firstPayload=results.find(item=>item.data&&!item.error)?.data||{};$('safety').innerHTML=safetyBar(firstPayload);};
  if(typeof TASK_PARAM_PRESETS!=='undefined'){TASK_PARAM_PRESETS.order_preview_dry_run={max_single_order_amount:1000,min_lot:100,lot_size:100,limit:5};}
  if(typeof TASK_PRIORITY!=='undefined'&&!TASK_PRIORITY.includes('order_preview_dry_run')){TASK_PRIORITY.splice(TASK_PRIORITY.indexOf('human_approval_review_dry_run')+1,0,'order_preview_dry_run');}
  if(typeof renderUpdatedArtifacts!=='undefined'){
    const oldRenderUpdatedArtifacts=renderUpdatedArtifacts;
    renderUpdatedArtifacts=async function(taskId){
      if(taskId==='order_preview_dry_run'){
        const status=await apiGet('/portfolio/status');
        const preview=await apiGet('/portfolio/order-preview/latest');
        const budget=await apiGet('/portfolio/budget/latest');
        return `<section class="task-artifact-preview"><h4>已写入 Portfolio 订单预览</h4>${renderMetricCards(status)}${renderRowsTable(preview.previews||[],'Order Preview')}${renderMetricCards(budget.budget||budget)}</section>`;
      }
      return oldRenderUpdatedArtifacts(taskId);
    };
  }
  buildNav();show('overview');
})();
