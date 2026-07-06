import { holdings, orders, strategies } from '../mock/mockData';
import type { RiskLevel, StrategyStatus } from '../types';
import { apiOrMock } from './apiClient';

function riskLevel(value: unknown): RiskLevel {
  const text = String(value ?? '').toUpperCase();
  if (text.includes('CRITICAL')) return 'CRITICAL';
  if (text.includes('HIGH') || text.includes('BLOCK')) return 'HIGH';
  if (text.includes('MEDIUM') || text.includes('WARN')) return 'MEDIUM';
  return 'LOW';
}

function normalizeStrategy(row: any): StrategyStatus {
  const rawStatus = String(row.status ?? '').toUpperCase();
  return {
    id: String(row.id ?? row.intent_id ?? row.symbol ?? row.name ?? ''),
    name: String(row.name ?? row.strategy ?? row.symbol ?? 'Backend Strategy'),
    type: String(row.type ?? 'backend_artifact'),
    mode: row.mode ?? '仿真',
    pool: String(row.pool ?? row.symbol ?? row.universe ?? ''),
    rebalance: String(row.rebalance ?? row.period ?? 'dry-run'),
    todayReturn: Number(row.todayReturn ?? 0),
    totalReturn: Number(row.totalReturn ?? 0),
    maxDrawdown: Number(row.maxDrawdown ?? 0),
    position: Number(row.position ?? row.targetWeight ?? row.target_weight ?? 0),
    signalCount: Number(row.signalCount ?? 1),
    riskStatus: riskLevel(row.riskStatus ?? row.risk_status ?? row.riskDecision),
    status: rawStatus.includes('PAUSE') ? 'PAUSED' : rawStatus.includes('STOP') ? 'STOPPED' : rawStatus.includes('SIM') ? 'SIMULATING' : 'RUNNING',
    sharpe: Number(row.sharpe ?? 0),
    lastAction: row.lastAction ?? row.action ?? row.signal,
    signal: row.signal,
    targetWeight: Number(row.targetWeight ?? row.target_weight ?? 0),
    source: row.source,
    sourcePath: row.sourcePath ?? row.source_path,
  };
}

export async function getStrategyList() {
  const rows = await apiOrMock('/strategies/list', strategies);
  return rows.map(normalizeStrategy);
}

export async function getStrategyDetail(id: string) {
  const list = await getStrategyList();
  return {
    strategy: list.find((item) => item.id === id) ?? list[0] ?? strategies[0],
    holdings: holdings.slice(0, 12),
    rebalanceOrders: orders.slice(0, 8),
  };
}

export async function getRebalancePlan() {
  const backendOrders = await apiOrMock('/execution/orders', orders.slice(0, 10));
  return { holdings: holdings.slice(0, 16), orders: backendOrders, riskPassed: false, notice: '调仓计划只进入风控闸门，不直接下单。' };
}
