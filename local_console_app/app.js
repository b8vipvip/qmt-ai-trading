const API='/api/v1';
const safetyKeys=['read_only','dry_run','live_disabled','no_order_submitted','requires_human_approval','account_masked','order_submit_enabled','order_cancel_enabled','real_order_submitted'];
const modules=[
 {id:'overview',name:'总览 / 工作流状态',eps:['/console/bootstrap','/workflow/status','/workflow/feature-matrix']},
 {id:'market',name:'QMT / xtdata 行情状态',eps:['/market/xtdata-live/status','/datahub/market/latest'],params:[['symbol','510300.SH'],['period','1d']]},
 {id:'datahub',name:'Data Hub 行情缓存',eps:['/datahub/status','/datahub/symbols','/datahub/cache/status','/datahub/market/latest']},
 {id:'research',name:'Research 因子研究',eps:['/research/context','/research/factors/latest','/research/candidates/latest']},
 {id:'strategy',name:'Strategy 策略信号',eps:['/strategy/context','/strategy/signals/latest','/strategy/trade-intents/latest']},
 {id:'risk',name:'Risk Gate 风控审查',eps:['/risk/context','/risk/decisions/latest','/risk/report/latest']},
 {id:'candidates',name:'候选池排名',eps:['/research/candidates/latest']},
 {id:'agent',name:'Agent 投研',eps:['/agents/context','/agents/report/latest']},
 {id:'backtest',name:'Backtest / Shadow Replay',eps:['/backtest/shadow-replay/latest']},
 {id:'intent',name:'TradeIntent dry-run',eps:['/strategy/trade-intents/latest']},
 {id:'paper',name:'Paper Trading / Shadow Replay',eps:['/paper-trading/status','/paper-trading/orders/latest','/paper-trading/positions/latest','/paper-trading/pnl/latest']},
 {id:'monitoring',name:'Monitoring / Alerts',eps:['/monitoring/context','/monitoring/alerts/latest','/monitoring/circuit-breaker/latest']},
 {id:'approval',name:'Human Approval 人工确认',eps:['/approval/status','/approval/requests/latest']},
 {id:'account',name:'Account Readonly / 持仓只读',eps:['/account-readonly/status','/account-readonly/diagnostics','/account-readonly/asset','/account-readonly/positions']},
 {id:'safety',name:'Safety / Live Disabled 安全边界',eps:['/safety/status','/live/status']}
];
async function get(p,query=''){const r=await fetch(API+p+query); if(!r.ok)throw new Error(`${p}: HTTP ${r.status}`); return r.json();}
function badge(v){const s=String(v); const cls=/false|DISABLED|DATA_MISSING|EMPTY|BLOCKED/.test(s)?'warn':'ok'; return `<span class="badge ${cls}">${s}</span>`}
function safetyBar(d={}){return safetyKeys.map(k=>`<span class="tag">${k}=${d[k]??(k.includes('enabled')||k.includes('submitted')?'false':'true')}</span>`).join('')}
function flattenRows(obj,prefix=''){let rows=[]; if(obj&&typeof obj==='object'&&!Array.isArray(obj)){for(const [k,v] of Object.entries(obj)){if(v&&typeof v==='object') rows.push([prefix+k, Array.isArray(v)?`Array(${v.length})`:'Object']); else rows.push([prefix+k, v]);}} return rows.slice(0,18);}
function primary(d){const rows=flattenRows(d); const empty=d.status==='DATA_MISSING'||d.status==='EMPTY'||JSON.stringify(d).includes('DATA_MISSING'); return `<div class="statusline">状态 ${badge(d.status||d.feature_status||'READY')} ${empty?badge('EMPTY/DATA_MISSING'):''}</div><table><tbody>${rows.map(([k,v])=>`<tr><th>${k}</th><td>${typeof v==='boolean'?badge(v):String(v)}</td></tr>`).join('')}</tbody></table>`}
function dataTable(d){let arr=Object.values(d).find(v=>Array.isArray(v)); if(!arr) return '<p class="empty">EMPTY/DATA_MISSING：暂无列表数据，已保持只读安全状态。</p>'; if(!arr.length) return '<p class="empty">EMPTY：列表为空。</p>'; const cols=[...new Set(arr.flatMap(x=>Object.keys(typeof x==='object'?x:{})))].slice(0,8); return `<table><thead><tr>${cols.map(c=>`<th>${c}</th>`).join('')}</tr></thead><tbody>${arr.slice(0,12).map(r=>`<tr>${cols.map(c=>`<td>${JSON.stringify(r[c]??'')}</td>`).join('')}</tr>`).join('')}</tbody></table>`}
function queryForm(m){return `<div class="query"><b>查询参数</b> ${(m.params||[]).map(([k,v])=>`<label>${k}<input id="q_${k}" value="${v}"></label>`).join('')} <button class="refresh" onclick="show('${m.id}')">刷新</button></div>`}
async function show(id){const m=modules.find(x=>x.id===id); document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.id===id)); app.innerHTML=`<section class="card"><h2>${m.name}</h2>${safetyBar()}${queryForm(m)}<p>加载中...</p></section>`; let query=''; if(m.params) query='?'+m.params.map(([k])=>`${encodeURIComponent(k)}=${encodeURIComponent(document.getElementById('q_'+k)?.value||'')}`).join('&'); const results=[]; for(const ep of m.eps){try{results.push([ep,await get(ep,query)]);}catch(e){results.push([ep,{ok:false,status:'DATA_MISSING',error:e.message,read_only:true,dry_run:true,live_disabled:true,no_order_submitted:true}]);}}
 app.innerHTML=`<section class="card hero"><h2>${m.name}</h2>${safetyBar(results[0]?.[1])}<p>正式启动：<code>py scripts\\run_console_api.py --host 127.0.0.1 --port 8768</code></p>${queryForm(m)}</section><section class="grid">${results.map(([ep,d])=>`<article class="card"><h3>${ep}</h3>${primary(d)}${dataTable(d)}<details><summary>调试 JSON</summary><pre>${JSON.stringify(d,null,2)}</pre></details></article>`).join('')}</section>`;}
nav.innerHTML=modules.map(m=>`<button data-id="${m.id}" onclick="show('${m.id}')">${m.name}</button>`).join('');
get('/health').then(h=>api.textContent='API 在线：'+h.service).catch(e=>api.textContent='API 离线：'+e.message); show('overview');
