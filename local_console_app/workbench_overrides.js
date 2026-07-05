(function(){
  const labels={ready:'已接入',partial:'部分接入',pending:'待接入'};
  const boards={
    overview:[['日常 dry-run 操作链路','ready','在总览页一键顺序运行行情、研究、策略、风控、Paper、人工复核和订单预览。'],['安全状态面板','ready','实时检查 can_submit_order、order_submit_enabled、real_order_submitted 等危险旗标。'],['实盘前安全审计','pending','后续接入 go/no-go 审计报告。'],['小资金灰度实盘','pending','必须在安全审计和人工确认后再进入。']],
    datahub:[['QMT 本地行情','ready','xtdata 只读行情和最新行情表已接入。'],['统一标的池','ready','datahub_symbols 已接入。'],['外部数据源','pending','AkShare / Tushare / BaoStock 待后端适配。'],['指数 / ETF / 行业 / 财务 / 新闻','pending','后续接入统一 Data Hub。']],
    research:[['基础多因子扫描','ready','factor_scan 已写入候选池。'],['ETF 研究评分','ready','候选池与评分可展示。'],['Alpha158 / Alpha360 / Alpha101','pending','标准因子库待接入。'],['LightGBM / Lasso / MLP','pending','模型训练与评分待接入。']],
    agent:[['技术面 Agent','partial','可消费行情与因子结果。'],['基本面 Agent','pending','依赖财务与行业数据。'],['情绪 / 新闻 Agent','pending','依赖新闻数据。'],['风险 / 组合 Agent','partial','可读取已有审查和组合预览产物。']],
    strategy:[['ETF 轮动','ready','候选和信号链路已接入。'],['多因子选股','partial','候选池到信号可联动。'],['buy / sell / hold 信号','ready','结构化信号可展示。'],['参数与版本管理','pending','后端待开发，当前只显示待接入状态。']]
  };
  function patch(id,name,lead){const m=modules.find(x=>x.id===id);if(m){if(name)m.name=name;if(lead)m.lead=lead;}}
  patch('overview','总览 / 日常工作台','一键运行 dry-run 链路，查看行情、研究、策略、风控、Paper、审批和组合预览的当前状态。');
  patch('datahub','Data Hub 数据源中心','统一管理行情、标的池、缓存和后续外部数据源；策略与 Agent 只能从 Data Hub 取数。');
  patch('agent','Agent 投研工作台','运行和查看 Agent 投研结果；只输出结构化建议，不允许跳过风控或直接下单。');
  patch('strategy','Strategy Engine 策略工作台','运行和查看策略信号、TradeIntent 与候选结果；策略输出必须进入 Risk Gate。');
  patch('tasks','任务执行 / 操作入口','选择白名单任务，确认参数后运行；所有任务保持只读 / dry-run / 不下单。');
  patch('safety','Safety / 安全边界','集中查看实盘、下单、撤单、自动批准和账户脱敏状态。');
  const overview=modules.find(x=>x.id==='overview');if(overview){overview.workflowPanel=true;}
  function boardHtml(id){const rows=boards[id];if(!rows)return'';return `<section class="card workbench-card"><div class="endpoint-head"><div><h3>模块能力地图</h3><p class="hint">已接入能力展示真实业务产物；未接入能力明确标注，不作为交易依据。</p></div>${badge('ok','工作台')}</div><div class="capability-grid">${rows.map(([t,s,d])=>`<div class="capability-item ${s}"><div class="capability-title">${escapeHtml(t)} ${badge(s==='pending'?'warn':'ok',labels[s])}</div><p>${escapeHtml(d)}</p></div>`).join('')}</div></section>`;}
  function heroHtml(module,state){return `<section class="card hero ${state.cls==='warn'?'pending':''}"><div class="module-title"><div><h2>${escapeHtml(module.name)}</h2><p>${escapeHtml(module.lead)}</p><p class="hint">当前页面直接读取业务接口和统一产物；能操作的模块会显示任务按钮，未接入的模块只显示待接入状态。</p></div>${badge(state.cls==='ok'?'ok':'warn',state.label)}</div><div class="module-safety">${safetyBar({})}</div>${queryForm(module)}</section>`;}
  show=async function(id){
    const module=modules.find(item=>item.id===id)||modules[0];
    document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.id===module.id||b.id===`nav_${module.id}`));
    const app=$('app');
    app.innerHTML='<section class="card">加载中...</section>';
    if(!module.eps?.length&&module.pendingItems){app.innerHTML=renderStatic(module);return;}
    const query=endpointQuery(module);
    const results=await loadModule(module,query);
    const state=moduleState(results);
    let html=heroHtml(module,state)+boardHtml(module.id);
    if(module.workflowPanel&&typeof renderWorkflowPanel==='function') html+=await renderWorkflowPanel();
    html+=module.taskPanel?await renderTaskPanel():`<section class="grid">${results.map(item=>renderEndpoint(item.endpoint,item.data)).join('')}</section>`;
    app.innerHTML=html;
    const firstPayload=results.find(item=>item.data&&!item.error)?.data||{};
    $('safety').innerHTML=safetyBar(firstPayload);
  };
  buildNav();show('overview');
})();