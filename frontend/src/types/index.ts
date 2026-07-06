export type StatusKind = 'normal' | 'warning' | 'danger' | 'offline';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type TradeMode = '研究' | '仿真' | '影子实盘' | '小资金实盘' | '正式实盘';

export interface MetricItem {
  title: string;
  value: string | number;
  change: string;
  status: StatusKind;
  trend: number[];
  source?: string;
}

export interface StrategyStatus {
  id: string;
  name: string;
  type: string;
  mode: TradeMode | '回测' | 'Paper';
  pool: string;
  rebalance: string;
  todayReturn: number;
  totalReturn: number;
  maxDrawdown: number;
  position: number;
  signalCount: number;
  riskStatus: RiskLevel;
  status: 'RUNNING' | 'PAUSED' | 'STOPPED' | 'SIMULATING';
  sharpe?: number;
  lastAction?: string;
  signal?: string;
  targetWeight?: number;
  source?: string;
  sourcePath?: string;
}

export interface EquityPoint {
  date: string;
  equity: number;
  benchmark: number;
  drawdown: number;
}

export interface SystemEvent {
  id: string;
  time: string;
  level: StatusKind;
  module: string;
  message: string;
  runId?: string;
  taskId?: string;
  sourcePath?: string;
}

export interface DataSourceStatus {
  name: string;
  status: StatusKind;
  updatedAt: string;
  records: number;
  latency: string;
  missingRate: number;
  abnormalRate: number;
  dataSource?: string;
  qualityLevel?: string;
  sourcePath?: string;
}

export interface DataQualityRow {
  dataset: string;
  tradeDate: string;
  stockCount: number;
  missingFields: number;
  abnormalValues: number;
  duplicateRows: number;
  passed: boolean;
  sourcePath?: string;
}

export interface DataTaskRow {
  name: string;
  type: string;
  cron: string;
  lastRun: string;
  nextRun: string;
  status: string;
  cost: string;
  sourcePath?: string;
}

export interface FactorRow {
  id: string;
  name: string;
  type: string;
  version: string;
  universe: string;
  icMean: number;
  rankIc: number;
  icir: number;
  longShortReturn: number;
  turnover: number;
  status: '研究中' | '候选' | '已上线' | '已下线';
  score?: number;
  rank?: number;
  reasons?: string;
  riskFlags?: string;
  sourcePath?: string;
}

export interface BacktestTask {
  id: string;
  name: string;
  strategy: string;
  universe: string;
  range: string;
  capital: number;
  rebalance: string;
  status: string;
  createdAt: string;
  cost: string;
  sourcePath?: string;
}

export interface HoldingRow {
  code: string;
  name: string;
  currentQty: number;
  currentWeight: number;
  targetWeight: number;
  targetValue: number;
  diffQty: number;
  diffAmount: number;
  riskStatus: RiskLevel;
  accountIdMasked?: string;
  sourcePath?: string;
}

export interface OrderRow {
  id: string;
  brokerOrderId?: string;
  strategy: string;
  code: string;
  name: string;
  side: '买入' | '卖出';
  rawSide?: string;
  quantity: number;
  price: number;
  type: string;
  amount: number;
  riskCheck: RiskLevel | 'PASS';
  riskDecision?: string;
  businessStatus?: string;
  status: string;
  createdAt: string;
  updatedAt?: string;
  intentId?: string;
  previewOnly?: boolean;
  canSubmit?: boolean;
  latestPrice?: number;
  estimatedAmount?: number;
  sourcePath?: string;
}

export interface TradeRow {
  id: string;
  orderId: string;
  code: string;
  name: string;
  side: '买入' | '卖出';
  quantity: number;
  price: number;
  amount: number;
  commission: number;
  stampTax: number;
  time: string;
  sourcePath?: string;
}

export interface RiskRule {
  id: string;
  name: string;
  type: '交易前' | '交易中' | '事后';
  threshold: string;
  current: string;
  action: '警告' | '拦截' | '降仓' | '停止交易' | '平仓';
  enabled: boolean;
  lastTriggered: string;
  description?: string;
  sourcePath?: string;
}

export interface RiskEvent {
  id: string;
  time: string;
  strategy: string;
  rule: string;
  level: RiskLevel;
  trigger: string;
  threshold: string;
  action: string;
  result: string;
  operator: string;
  sourcePath?: string;
}
