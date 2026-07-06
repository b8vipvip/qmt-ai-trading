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
  RiskLevel,
  RiskRule,
  StatusKind,
  StrategyStatus,
  SystemEvent,
} from '../types';

function num(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function str(value: unknown, fallback = ''): string {
  if (value === undefined || value === null) return fallback;
  return String(value);
}

function arr<T = any>(value: unknown): T[] {
  return Array.isArray(value) ? value as T[] : [];
}

export function statusKind(value: unknown): StatusKind {
  const text = str(value).toUpperCase();
  if (text.includes('CRITICAL') || text.includes('ERROR') || text.includes('FAILED')) return 'danger';
  if (text.includes('WARN') || text.includes('MEDIUM') || text.includes('LOCK') || text.includes('OFFLINE')) return 'warning';
  if (text.includes('DISABLED') || text.includes('EMPTY') || text.includes('MISSING')) return 'offline';
  return 'normal';
}

export function riskLevel(value: unknown): RiskLevel {
  const text = str(value).toUpperCase();
  if (text.includes('CRITICAL')) return 'CRITICAL';
  if (text.includes('HIGH') || text.includes('BLOCK')) return 'HIGH';
  if (text.includes('MEDIUM') || text.includes('WARN')) return 'MEDIUM';
  return 'LOW';
}

export function sideName(value: unknown): '买入' | '卖出' {
  const text = str(value).toUpperCase();
  return text === 'SELL' || text.includes('卖') ? '卖出' : '买入';
}

export function riskCheckName(value: unknown): OrderRow['riskCheck'] {
  const text = str(value).toUpperCase();
  if (text.includes('PASS')) return 'PASS';
  return riskLevel(text);
}

export function mapMetrics(data: any, fallback: MetricItem[] = []): MetricItem[] {
  const rows = arr<any>(data?.metrics ?? data);
  if (!rows.length) return fallback;
  return rows.map((m) => ({
    title: str(m.title ?? m.name),
    value: m.value ?? '',
    change: str(m.change ?? m.delta ?? ''),
    status: statusKind(m.status),
    trend: arr<number>(m.trend).map((x) => num(x)),
    source: m.source,
  }));
}

export function mapRiskOverview(data: any, fallback: any = {}): any {
  const raw = data?.riskOverview ?? data ?? fallback;
  return {
    ...fallback,
    ...raw,
    level: str(raw.level ?? fallback.level ?? 'LOW'),
    triggerCount: num(raw.triggerCount ?? raw.trigger_count ?? fallback.triggerCount),
    blockedOrders: num(raw.blockedOrders ?? raw.blocked_orders ?? fallback.blockedOrders),
    totalPosition: num(raw.totalPosition ?? raw.total_position ?? raw.total ?? fallback.totalPosition),
    maxSinglePosition: num(raw.maxSinglePosition ?? raw.max_single_position ?? fallback.maxSinglePosition),
    maxIndustryExposure: num(raw.maxIndustryExposure ?? raw.max_industry_exposure ?? fallback.maxIndustryExposure),
    intradayLoss: num(raw.intradayLoss ?? raw.intraday_loss ?? raw.dayLoss ?? fallback.intradayLoss),
    currentDrawdown: num(raw.currentDrawdown ?? raw.current_drawdown ?? fallback.currentDrawdown),
    losingDays: num(raw.losingDays ?? raw.losing_days ?? fallback.losingDays),
    concentration: num(raw.concentration ?? fallback.concentration),
    industry: num(raw.industry ?? fallback.industry),
    total: num(raw.total ?? raw.totalPosition ?? fallback.total),
    dayLoss: num(raw.dayLoss ?? raw.intradayLoss ?? fallback.dayLoss),
    abnormalOrders: num(raw.abnormalOrders ?? raw.abnormal_orders ?? fallback.abnormalOrders),
    disconnects: num(raw.disconnects ?? fallback.disconnects),
  };
}

export function mapDashboardOverview(data: any, fallback: any) {
  return {
    metrics: mapMetrics(data, fallback.metrics),
    riskOverview: mapRiskOverview(data?.riskOverview ?? data, fallback.riskOverview),
  };
}

export function mapStrategyStatusList(data: any, fallback: StrategyStatus[] = []): StrategyStatus[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row, i) => {
    const rawStatus = str(row.status).toUpperCase();
    return {
      id: str(row.id ?? row.intent_id ?? row.symbol ?? row.name ?? `strategy-${i + 1}`),
      name: str(row.name ?? row.strategy ?? row.symbol ?? 'Backend Strategy'),
      type: str(row.type ?? row.strategy_type ?? '后端产物'),
      mode: row.mode ?? '仿真',
      pool: str(row.pool ?? row.symbol ?? row.universe ?? ''),
      rebalance: str(row.rebalance ?? row.period ?? 'dry-run'),
      todayReturn: num(row.todayReturn ?? row.today_return),
      totalReturn: num(row.totalReturn ?? row.total_return),
      maxDrawdown: num(row.maxDrawdown ?? row.max_drawdown),
      position: num(row.position ?? row.targetWeight ?? row.target_weight),
      signalCount: num(row.signalCount ?? row.signal_count ?? 1),
      riskStatus: riskLevel(row.riskStatus ?? row.risk_status ?? row.riskDecision),
      status: rawStatus.includes('PAUSE') ? 'PAUSED' : rawStatus.includes('STOP') ? 'STOPPED' : rawStatus.includes('SIM') ? 'SIMULATING' : 'RUNNING',
      sharpe: num(row.sharpe),
      lastAction: str(row.lastAction ?? row.last_action ?? row.action ?? row.signal),
      signal: row.signal,
      targetWeight: num(row.targetWeight ?? row.target_weight),
      source: row.source,
      sourcePath: row.sourcePath ?? row.source_path,
    };
  });
}

export function mapEquityCurve(data: any, fallback: EquityPoint[] = []): EquityPoint[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row) => ({
    date: str(row.date ?? row.time),
    equity: num(row.equity ?? row.nav ?? row.total_value),
    benchmark: num(row.benchmark ?? row.hs300 ?? row.index),
    drawdown: num(row.drawdown ?? row.max_drawdown),
  }));
}

export function mapSystemEvents(data: any, fallback: SystemEvent[] = []): SystemEvent[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row, i) => ({
    id: str(row.id ?? row.run_id ?? `event-${i + 1}`),
    time: str(row.time ?? row.finished_at ?? row.started_at),
    level: statusKind(row.level ?? row.status),
    module: str(row.module ?? row.category ?? row.task_id ?? 'SYSTEM'),
    message: str(row.message ?? row.task_name ?? row.task_id ?? '系统事件'),
    runId: row.runId ?? row.run_id,
    taskId: row.taskId ?? row.task_id,
    sourcePath: row.sourcePath ?? row.source_path,
  }));
}

export function mapDataSources(data: any, fallback: DataSourceStatus[] = []): DataSourceStatus[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row) => ({
    name: str(row.name ?? row.dataset ?? row.source),
    status: statusKind(row.status),
    updatedAt: str(row.updatedAt ?? row.updated_at ?? row.time),
    records: num(row.records ?? row.record_count ?? row.count),
    latency: str(row.latency ?? row.delay ?? '-'),
    missingRate: num(row.missingRate ?? row.missing_rate),
    abnormalRate: num(row.abnormalRate ?? row.abnormal_rate),
    dataSource: row.dataSource ?? row.data_source,
    qualityLevel: row.qualityLevel ?? row.quality_level,
    sourcePath: row.sourcePath ?? row.source_path,
  }));
}

export function mapDataQualityRows(data: any, fallback: DataQualityRow[] = []): DataQualityRow[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row) => ({
    dataset: str(row.dataset ?? row.name),
    tradeDate: str(row.tradeDate ?? row.trade_date ?? row.date),
    stockCount: num(row.stockCount ?? row.stock_count ?? row.symbol_count),
    missingFields: num(row.missingFields ?? row.missing_fields),
    abnormalValues: num(row.abnormalValues ?? row.abnormal_values),
    duplicateRows: num(row.duplicateRows ?? row.duplicate_rows),
    passed: Boolean(row.passed ?? row.ok ?? false),
    sourcePath: row.sourcePath ?? row.source_path,
  }));
}

export function mapDataTasks(data: any, fallback: DataTaskRow[] = []): DataTaskRow[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row) => ({
    name: str(row.name ?? row.task_name ?? row.task_id),
    type: str(row.type ?? row.category),
    cron: str(row.cron ?? row.schedule ?? '-'),
    lastRun: str(row.lastRun ?? row.last_run ?? row.finished_at),
    nextRun: str(row.nextRun ?? row.next_run),
    status: str(row.status ?? 'UNKNOWN'),
    cost: str(row.cost ?? row.duration ?? ''),
    sourcePath: row.sourcePath ?? row.source_path,
  }));
}

export function mapFactorRows(data: any, fallback: FactorRow[] = []): FactorRow[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row, i) => ({
    id: str(row.id ?? row.factor_id ?? row.symbol ?? `factor-${i + 1}`),
    name: str(row.name ?? row.factor_name ?? row.symbol ?? '因子评分'),
    type: str(row.type ?? row.factor_type ?? '多因子'),
    version: str(row.version ?? 'backend'),
    universe: str(row.universe ?? row.symbol ?? 'backend_artifacts'),
    icMean: num(row.icMean ?? row.ic_mean),
    rankIc: num(row.rankIc ?? row.rank_ic),
    icir: num(row.icir),
    longShortReturn: num(row.longShortReturn ?? row.long_short_return),
    turnover: num(row.turnover),
    status: (row.status ?? '候选') as FactorRow['status'],
    score: num(row.score),
    rank: num(row.rank ?? i + 1),
    reasons: str(row.reasons),
    riskFlags: str(row.riskFlags ?? row.risk_flags),
    sourcePath: row.sourcePath ?? row.source_path,
  }));
}

export function mapHoldingRows(data: any, fallback: HoldingRow[] = []): HoldingRow[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row, i) => ({
    code: str(row.code ?? row.symbol ?? `POS-${i + 1}`),
    name: str(row.name ?? row.symbol ?? row.code ?? ''),
    currentQty: num(row.currentQty ?? row.current_qty ?? row.quantity ?? row.volume),
    currentWeight: num(row.currentWeight ?? row.current_weight),
    targetWeight: num(row.targetWeight ?? row.target_weight),
    targetValue: num(row.targetValue ?? row.target_value),
    diffQty: num(row.diffQty ?? row.diff_qty),
    diffAmount: num(row.diffAmount ?? row.diff_amount),
    riskStatus: riskLevel(row.riskStatus ?? row.risk_status),
    accountIdMasked: row.accountIdMasked ?? row.account_id_masked,
    sourcePath: row.sourcePath ?? row.source_path,
  }));
}

export function mapOrderRows(data: any, fallback: OrderRow[] = []): OrderRow[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row) => {
    const riskDecision = row.riskDecision ?? row.riskCheck ?? row.risk_decision ?? row.risk_check ?? '';
    const price = num(row.price ?? row.latestPrice ?? row.latest_price);
    const amount = num(row.amount ?? row.estimatedAmount ?? row.estimated_amount);
    return {
      id: str(row.id ?? row.preview_id ?? row.order_id ?? row.intent_id),
      brokerOrderId: row.brokerOrderId ?? row.broker_order_id,
      strategy: str(row.strategy ?? row.intent_id ?? row.strategy_name ?? 'backend_artifact'),
      code: str(row.code ?? row.symbol),
      name: str(row.name ?? row.symbol ?? row.code),
      side: sideName(row.side ?? row.rawSide),
      rawSide: str(row.rawSide ?? row.side),
      quantity: num(row.quantity ?? row.preview_quantity ?? row.order_quantity),
      price,
      type: str(row.type ?? row.order_type ?? 'PREVIEW'),
      amount,
      riskCheck: riskCheckName(riskDecision),
      riskDecision: str(riskDecision),
      businessStatus: str(row.businessStatus ?? row.business_status ?? row.status),
      status: str(row.status ?? row.businessStatus ?? 'PREVIEW'),
      createdAt: str(row.createdAt ?? row.created_at),
      updatedAt: row.updatedAt ?? row.updated_at,
      intentId: row.intentId ?? row.intent_id,
      previewOnly: row.previewOnly ?? row.preview_only ?? true,
      canSubmit: Boolean(row.canSubmit ?? row.can_submit ?? false),
      latestPrice: num(row.latestPrice ?? row.latest_price ?? price),
      estimatedAmount: num(row.estimatedAmount ?? row.estimated_amount ?? amount),
      sourcePath: row.sourcePath ?? row.source_path,
    };
  });
}

export function mapRiskRules(data: any, fallback: RiskRule[] = []): RiskRule[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row) => ({
    id: str(row.id ?? row.rule_id ?? row.name),
    name: str(row.name ?? row.rule_name),
    type: (row.type ?? row.rule_type ?? '交易前') as RiskRule['type'],
    threshold: str(row.threshold ?? row.limit),
    current: str(row.current ?? row.current_value),
    action: (row.action ?? '拦截') as RiskRule['action'],
    enabled: Boolean(row.enabled ?? true),
    lastTriggered: str(row.lastTriggered ?? row.last_triggered),
    description: row.description,
    sourcePath: row.sourcePath ?? row.source_path,
  }));
}

export function mapRiskEvents(data: any, fallback: RiskEvent[] = []): RiskEvent[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row, i) => ({
    id: str(row.id ?? row.intent_id ?? row.event_id ?? `risk-${i + 1}`),
    time: str(row.time ?? row.created_at),
    strategy: str(row.strategy ?? row.intent_id),
    rule: str(row.rule ?? row.rule_name ?? 'Risk Gate'),
    level: riskLevel(row.level ?? row.risk_level ?? row.decision),
    trigger: str(row.trigger ?? row.trigger_value ?? row.decision),
    threshold: str(row.threshold ?? 'safety_policy'),
    action: str(row.action ?? row.decision),
    result: str(row.result ?? row.decision),
    operator: str(row.operator ?? 'system'),
    sourcePath: row.sourcePath ?? row.source_path,
  }));
}

export function mapBacktestTasks(data: any, fallback: BacktestTask[] = []): BacktestTask[] {
  const rows = arr<any>(data);
  if (!rows.length) return fallback;
  return rows.map((row, i) => ({
    id: str(row.id ?? row.task_id ?? `backtest-${i + 1}`),
    name: str(row.name ?? row.task_name ?? 'Backtest Task'),
    strategy: str(row.strategy ?? row.strategy_name),
    universe: str(row.universe ?? row.pool),
    range: str(row.range ?? row.date_range),
    capital: num(row.capital ?? row.initial_cash),
    rebalance: str(row.rebalance ?? row.period),
    status: str(row.status),
    createdAt: str(row.createdAt ?? row.created_at),
    cost: str(row.cost ?? row.duration),
    sourcePath: row.sourcePath ?? row.source_path,
  }));
}
