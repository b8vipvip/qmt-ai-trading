const XTDATA_APIS = [
  'GET /api/v1/market/xtdata/context',
  'GET /api/v1/market/xtdata/config',
  'GET /api/v1/market/xtdata/import-guard',
  'GET /api/v1/market/xtdata/capability-probe',
  'GET /api/v1/market/xtdata/safety',
  'GET /api/v1/market/xtdata/report',
  'POST /api/v1/tasks/run task_id=xtdata_boundary_dry_run'
];
const XTDATA_FLAGS = 'enabled=false dry_run=true read_only=true xtdata_imported=false mini_qmt_connected=false real_market_data=false sandbox_fallback=true allow_xttrader=false no_order_submitted=true no_qmt_trader_api=true';
function renderXtdataBoundaryChecklist(){return ['xtdata 边界检查','xtdata adapter 当前状态','配置开关表','Import Guard 检查结果','MiniQMT 连接状态 dry-run','真实行情权限 dry-run','Sandbox fallback 状态','Safety Gate 结果','下一阶段启用清单','安全边界说明',...XTDATA_APIS,XTDATA_FLAGS].join('\n');}
window.renderXtdataBoundaryChecklist = renderXtdataBoundaryChecklist;
