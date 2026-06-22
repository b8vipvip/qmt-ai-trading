const XTDATA_ENABLE_APIS = [
  'GET /api/v1/market/xtdata-enable/context','GET /api/v1/market/xtdata-enable/request','GET /api/v1/market/xtdata-enable/environment','GET /api/v1/market/xtdata-enable/checklist','GET /api/v1/market/xtdata-enable/audit','GET /api/v1/market/xtdata-enable/decision','GET /api/v1/market/xtdata-enable/report','POST /api/v1/tasks/run task_id=xtdata_enable_dry_run'
];
const XTDATA_ENABLE_FLAGS = 'enable_xtdata=false real_market_data=false mini_qmt_connected=false xtdata_imported=false read_only=true dry_run=true requires_human_confirmation=true manual_confirmation_completed=false allow_xttrader=false';
function renderXtdataEnableChecklist(){return ['xtdata 启用确认','xtdata 启用请求状态','环境检测结果','人工确认 checklist','配置审计表','安全阻断原因','sandbox fallback 状态','下一阶段计划','安全边界说明','decision READY_FOR_MANUAL_REVIEW',...XTDATA_ENABLE_APIS,XTDATA_ENABLE_FLAGS].join('\n');}
window.renderXtdataEnableChecklist = renderXtdataEnableChecklist;
