import type {
  BacktestTask,
  DataQualityRow,
  DataSourceStatus,
  DataTaskRow,
  EquityPoint,
  FactorRow,
  HoldingRow,
  MetricItem,
  OrderRow,
  RiskEvent,
  RiskRule,
  StrategyStatus,
  SystemEvent,
} from '../types';

const stockNames = ['平安银行','万科A','招商银行','贵州茅台','五粮液','宁德时代','比亚迪','中信证券','东方财富','中国平安','恒瑞医药','隆基绿能','紫金矿业','中国中免','海康威视','美的集团','立讯精密','京东方A','格力电器','伊利股份','中芯国际','药明康德','三一重工','海尔智家','长江电力','中国神华','中国移动','中国石油','中国海油','工业富联','迈瑞医疗','泸州老窖','山西汾酒','阳光电源','爱尔眼科','科大讯飞','韦尔股份','北方华创','中国建筑','中国中铁','中际旭创','寒武纪','赛力斯','长安汽车','TCL科技','包钢股份','牧原股份','温氏股份','海光信息','中信建投'];

export const metrics: MetricItem[] = [
  { title: '今日收益', value: '+0.86%', change: '+12.4bp', status: 'normal', trend: [2, 4, 3, 7, 8, 9, 12] },
  { title: '累计收益', value: '+31.28%', change: '+1.9%', status: 'normal', trend: [20, 21, 22, 24, 26, 30, 31] },
  { title: '当前总资产', value: '¥5,200,192', change: '+¥44,120', status: 'normal', trend: [480, 488, 492, 501, 506, 516, 520] },
  { title: '当前仓位', value: '62.8%', change: '-3.1%', status: 'warning', trend: [68, 67, 66, 65, 63, 62, 63] },
  { title: '今日成交额', value: '¥386,400', change: '+18.2%', status: 'normal', trend: [12, 16, 22, 19, 31, 35, 38] },
  { title: '当前最大回撤', value: '-4.12%', change: '+0.3%', status: 'warning', trend: [2, 3, 4, 5, 4, 4.2, 4.1] },
  { title: '运行策略数', value: 8, change: '0', status: 'normal', trend: [8, 8, 8, 8, 8, 8, 8] },
  { title: '当前风险等级', value: 'MEDIUM', change: '可控', status: 'warning', trend: [1, 1, 2, 2, 2, 2, 2] },
];

export const strategies: StrategyStatus[] = [
  { id: 's1', name: '沪深300 ETF 动量轮动', type: 'ETF轮动', mode: '影子实盘', pool: 'ETF核心池', rebalance: '周频', todayReturn: 0.42, totalReturn: 18.7, maxDrawdown: -3.8, position: 72, signalCount: 4, riskStatus: 'LOW', status: 'RUNNING', sharpe: 1.82 },
  { id: 's2', name: '中证500 多因子增强', type: '多因子', mode: '仿真', pool: '中证500', rebalance: '月频', todayReturn: 0.68, totalReturn: 25.1, maxDrawdown: -6.2, position: 58, signalCount: 12, riskStatus: 'MEDIUM', status: 'RUNNING', sharpe: 1.64 },
  { id: 's3', name: '红利低波组合', type: '多因子', mode: '小资金实盘', pool: '红利低波', rebalance: '月频', todayReturn: -0.12, totalReturn: 11.5, maxDrawdown: -2.9, position: 44, signalCount: 2, riskStatus: 'LOW', status: 'RUNNING', sharpe: 1.21 },
  { id: 's4', name: '科创成长趋势', type: '趋势', mode: 'Paper', pool: '科创50', rebalance: '日频', todayReturn: 1.18, totalReturn: 9.3, maxDrawdown: -8.5, position: 35, signalCount: 8, riskStatus: 'HIGH', status: 'SIMULATING', sharpe: 0.92 },
  { id: 's5', name: '事件驱动公告策略', type: '事件', mode: '研究', pool: '全A', rebalance: '事件触发', todayReturn: 0, totalReturn: 0, maxDrawdown: 0, position: 0, signalCount: 6, riskStatus: 'MEDIUM', status: 'PAUSED', sharpe: 0 },
  { id: 's6', name: 'AI Alpha 混合模型', type: '机器学习', mode: '仿真', pool: '沪深300', rebalance: '周频', todayReturn: 0.73, totalReturn: 14.6, maxDrawdown: -5.4, position: 66, signalCount: 15, riskStatus: 'MEDIUM', status: 'RUNNING', sharpe: 1.47 },
  { id: 's7', name: '北向资金跟随', type: '资金流', mode: '影子实盘', pool: '陆股通', rebalance: '日频', todayReturn: -0.32, totalReturn: 7.2, maxDrawdown: -4.6, position: 48, signalCount: 5, riskStatus: 'MEDIUM', status: 'RUNNING', sharpe: 1.02 },
  { id: 's8', name: '行业轮动防御组合', type: '行业轮动', mode: '回测', pool: '行业ETF', rebalance: '周频', todayReturn: 0.21, totalReturn: 19.2, maxDrawdown: -3.1, position: 0, signalCount: 0, riskStatus: 'LOW', status: 'STOPPED', sharpe: 1.76 },
];

export const equityCurve: EquityPoint[] = Array.from({ length: 180 }).map((_, i) => {
  const equity = 100 + i * 0.17 + Math.sin(i / 8) * 2.4 + Math.max(0, i - 120) * 0.06;
  const benchmark = 100 + i * 0.07 + Math.sin(i / 10) * 1.8;
  const peak = 100 + i * 0.18;
  return { date: `D-${179 - i}`, equity: Number(equity.toFixed(2)), benchmark: Number(benchmark.toFixed(2)), drawdown: Number(((equity - peak) / peak * 100).toFixed(2)) };
});

export const systemEvents: SystemEvent[] = Array.from({ length: 30 }).map((_, i) => ({
  id: `evt-${i + 1}`,
  time: `09:${String(30 + i).padStart(2, '0')}:18`,
  level: i % 11 === 0 ? 'danger' : i % 5 === 0 ? 'warning' : 'normal',
  module: ['行情','策略','风控','订单','数据','监控'][i % 6],
  message: ['行情连接成功','策略生成 3 条信号','风控拦截一笔超仓订单','订单计划已生成但未提交','数据同步完成','接口延迟恢复正常'][i % 6],
}));

export const riskOverview = {
  level: 'MEDIUM', triggerCount: 6, blockedOrders: 2, totalPosition: 62.8, maxSinglePosition: 8.4,
  maxIndustryExposure: 21.5, intradayLoss: -0.36, currentDrawdown: -4.12, losingDays: 1,
  concentration: 42, industry: 55, total: 63, dayLoss: 23, abnormalOrders: 2, disconnects: 1,
};

export const dataSources: DataSourceStatus[] = ['Tick数据','Level2数据','日线数据','分钟线数据','基本面数据','公告数据','新闻数据','资金流数据'].map((name, i) => ({
  name,
  status: i === 1 ? 'offline' : i === 6 ? 'warning' : 'normal',
  updatedAt: `2026-07-05 ${String(14 + i).padStart(2, '0')}:30`,
  records: 120000 + i * 18000,
  latency: i === 1 ? '未接入' : `${80 + i * 35}ms`,
  missingRate: Number((i * 0.12).toFixed(2)),
  abnormalRate: Number((i * 0.07).toFixed(2)),
}));

export const dataQuality: DataQualityRow[] = ['daily_bar','minute_bar','fundamental','announcement','news','money_flow'].map((dataset, i) => ({ dataset, tradeDate: '2026-07-05', stockCount: 5200 - i * 60, missingFields: i, abnormalValues: i * 7, duplicateRows: i % 2, passed: i < 4 }));
export const dataTasks: DataTaskRow[] = ['日线同步','分钟线补齐','基本面更新','新闻抓取','数据质量校验'].map((name, i) => ({ name, type: ['同步','清洗','计算','采集','校验'][i], cron: ['每日收盘','每15分钟','每日凌晨','实时','每日收盘'][i], lastRun: `2026-07-05 ${10 + i}:00`, nextRun: `2026-07-06 ${10 + i}:00`, status: i === 3 ? 'RUNNING' : 'SUCCESS', cost: `${18 + i * 9}s` }));

export const factors: FactorRow[] = ['价值低估','动量20日','质量ROE','低波动','资金流强度','盈利修正','换手率反转','行业景气','北向增持','公告情绪'].map((name, i) => ({
  id: `factor-${i + 1}`, name, type: ['价值','动量','质量','波动率','资金流','自定义'][i % 6], version: `v${1 + (i % 3)}.${i}`, universe: i % 2 ? '中证500' : '沪深300',
  icMean: Number((0.025 + i * 0.004).toFixed(3)), rankIc: Number((0.032 + i * 0.003).toFixed(3)), icir: Number((0.7 + i * 0.08).toFixed(2)),
  longShortReturn: Number((4.8 + i * 0.9).toFixed(2)), turnover: Number((18 + i * 2.3).toFixed(1)), status: ['研究中','候选','已上线','已下线'][i % 4] as FactorRow['status'],
}));

export const holdings: HoldingRow[] = Array.from({ length: 50 }).map((_, i) => ({
  code: `${String(600000 + i).padStart(6, '0')}.SH`, name: stockNames[i], currentQty: (i + 1) * 100, currentWeight: Number((0.4 + (i % 8) * 0.38).toFixed(2)), targetWeight: Number((0.5 + (i % 10) * 0.42).toFixed(2)), targetValue: 20000 + i * 1300, diffQty: (i % 5 - 2) * 100, diffAmount: (i % 5 - 2) * 3200, riskStatus: ['LOW','LOW','MEDIUM','HIGH','LOW'][i % 5] as HoldingRow['riskStatus'],
}));

export const orders: OrderRow[] = Array.from({ length: 20 }).map((_, i) => ({
  id: `ORD-${String(i + 1).padStart(4, '0')}`, brokerOrderId: i > 4 ? `BRK-${10000 + i}` : undefined, strategy: strategies[i % strategies.length].name, code: holdings[i].code, name: holdings[i].name,
  side: i % 3 === 0 ? '卖出' : '买入', quantity: (i + 1) * 100, price: Number((8 + i * 0.73).toFixed(2)), type: i % 2 ? 'LIMIT' : 'TWAP', amount: Number(((i + 1) * 100 * (8 + i * 0.73)).toFixed(2)),
  riskCheck: i % 7 === 0 ? 'HIGH' : 'PASS', status: ['CREATED','RISK_CHECKED','SENT','ACCEPTED','PARTIAL_FILLED','FILLED','CANCELLED','REJECTED','FAILED'][i % 9], createdAt: `2026-07-05 10:${String(i + 10).padStart(2, '0')}`, updatedAt: `2026-07-05 10:${String(i + 12).padStart(2, '0')}`,
}));

export const trades = Array.from({ length: 30 }).map((_, i) => ({
  id: `TRD-${String(i + 1).padStart(4, '0')}`, orderId: orders[i % orders.length].id, code: holdings[i % holdings.length].code, name: holdings[i % holdings.length].name, side: i % 2 ? '卖出' : '买入', quantity: (i + 1) * 100, price: Number((7.8 + i * 0.61).toFixed(2)), amount: Number(((i + 1) * 100 * (7.8 + i * 0.61)).toFixed(2)), commission: Number((5 + i * 0.8).toFixed(2)), stampTax: i % 2 ? Number((3 + i * 0.5).toFixed(2)) : 0, time: `2026-07-05 11:${String(i + 1).padStart(2, '0')}:08`,
}));

export const riskRules: RiskRule[] = ['单票持仓上限','行业暴露上限','当日亏损限制','最大回撤限制','重复订单拦截','流动性过滤','黑名单禁买','接口断联熔断'].map((name, i) => ({
  id: `rule-${i + 1}`, name, type: ['交易前','交易中','事后'][i % 3] as RiskRule['type'], threshold: ['10%','25%','2%','8%','1次','成交额>500万','黑名单','3次/分钟'][i], current: ['8.4%','21.5%','0.36%','4.12%','0','通过','无','1'][i], action: ['拦截','降仓','停止交易','警告','拦截','警告','拦截','停止交易'][i] as RiskRule['action'], enabled: i !== 6, lastTriggered: i % 2 ? '未触发' : '2026-07-05 10:18',
}));

export const riskEvents: RiskEvent[] = Array.from({ length: 20 }).map((_, i) => ({
  id: `risk-${i + 1}`, time: `2026-07-05 ${9 + (i % 6)}:${String(10 + i).padStart(2, '0')}`, strategy: strategies[i % strategies.length].name, rule: riskRules[i % riskRules.length].name, level: ['LOW','MEDIUM','HIGH','CRITICAL'][i % 4] as RiskEvent['level'], trigger: `${5 + i}%`, threshold: `${8 + i % 3}%`, action: ['警告','拦截','降仓','停止交易'][i % 4], result: i % 5 === 0 ? '已拦截' : '已记录', operator: i % 3 === 0 ? 'system' : 'risk-bot',
}));

export const backtestTasks: BacktestTask[] = ['沪深300增强回测','ETF轮动回测','红利低波回测','AI Alpha 回测','科创趋势回测'].map((name, i) => ({ id: `bt-${i + 1}`, name, strategy: strategies[i].name, universe: strategies[i].pool, range: `2021-01-01 ~ 2026-07-05`, capital: 1000000 + i * 500000, rebalance: strategies[i].rebalance, status: i === 3 ? 'RUNNING' : 'SUCCESS', createdAt: `2026-07-0${i + 1}`, cost: `${12 + i * 6}m` }));

export const deploymentStages = ['Paper Trading','Shadow Trading','Small Capital','Full Live'].map((stage, i) => ({
  stage, status: ['RUNNING','READY','LOCKED','HIGH_RISK_LOCKED'][i], startedAt: i < 2 ? '2026-06-23' : '-', days: i < 2 ? 12 + i : 0, strategyCount: i < 2 ? 3 + i : 0, capital: ['0','0','¥100,000','需风控委员会审批'][i], issues: ['信号正常，待满 20 个交易日','理论订单生成正常','等待小资金授权','禁止一键开启'][i],
  criteria: [['连续运行20个交易日','无系统崩溃','信号生成正常','回测和仿真差异可解释'],['实盘行情稳定','理论订单生成正常','无重复信号','理论成交偏差可接受'],['连续运行1-3个月','最大回撤低于阈值','滑点低于预期','无严重风控事件'],['风控委员会审批','多签确认','小资金阶段验收通过','高危权限隔离']][i],
}));
