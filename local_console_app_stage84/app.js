const MARKET_APIS = [
  'GET /api/v1/market/sandbox/context',
  'GET /api/v1/market/sandbox/symbols',
  'GET /api/v1/market/sandbox/snapshots',
  'GET /api/v1/market/sandbox/bars',
  'GET /api/v1/market/sandbox/replay/latest',
  'GET /api/v1/market/sandbox/quality/latest',
  'GET /api/v1/market/sandbox/report/latest',
  'POST /api/v1/tasks/run task_id=market_replay_sandbox'
];
const SAFETY_FLAGS = 'sandbox=true mock_data=true read_only=true not_live_trading=true no_qmt_trader_api=true no_order_submitted=true';
function renderMarketReplayDashboard(){return ['行情回放','Provider 类型显示','标的列表','行情快照表','K线数据表','Replay Bus 状态','Replay Event 时间线','数据质量报告','安全边界说明','下一阶段真实 xtdata 接入边界说明',...MARKET_APIS,SAFETY_FLAGS].join('\n');}
window.renderMarketReplayDashboard = renderMarketReplayDashboard;
