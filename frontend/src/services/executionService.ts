import { holdings, orders, trades } from '../mock/mockData';
import type { OrderRow } from '../types';
import { apiOrMock, postMockAction } from './apiClient';

function sideName(value: unknown): '买入' | '卖出' {
  const text = String(value ?? '').toUpperCase();
  return text === 'SELL' || text.includes('卖') ? '卖出' : '买入';
}

function riskName(value: unknown): OrderRow['riskCheck'] {
  const text = String(value ?? '').toUpperCase();
  if (text.includes('PASS')) return 'PASS';
  if (text.includes('CRITICAL')) return 'CRITICAL';
  if (text.includes('HIGH')) return 'HIGH';
  if (text.includes('MEDIUM') || text.includes('WARN')) return 'MEDIUM';
  return 'LOW';
}

function normalizeOrder(row: any): OrderRow {
  const riskDecision = row.riskDecision ?? row.riskCheck ?? row.risk_decision ?? row.risk_check ?? '';
  const price = Number(row.price ?? row.latestPrice ?? row.latest_price ?? 0);
  const amount = Number(row.amount ?? row.estimatedAmount ?? row.estimated_amount ?? 0);
  return {
    id: String(row.id ?? row.preview_id ?? row.order_id ?? row.intent_id ?? ''),
    brokerOrderId: row.brokerOrderId ?? row.broker_order_id,
    strategy: String(row.strategy ?? row.intent_id ?? row.strategy_name ?? 'backend_artifact'),
    code: String(row.code ?? row.symbol ?? ''),
    name: String(row.name ?? row.symbol ?? row.code ?? ''),
    side: sideName(row.side ?? row.rawSide),
    rawSide: String(row.rawSide ?? row.side ?? ''),
    quantity: Number(row.quantity ?? row.preview_quantity ?? row.order_quantity ?? 0),
    price,
    type: String(row.type ?? row.order_type ?? 'PREVIEW'),
    amount,
    riskCheck: riskName(riskDecision),
    riskDecision: String(riskDecision),
    businessStatus: String(row.businessStatus ?? row.business_status ?? row.status ?? ''),
    status: String(row.status ?? row.businessStatus ?? 'PREVIEW'),
    createdAt: String(row.createdAt ?? row.created_at ?? ''),
    updatedAt: row.updatedAt ?? row.updated_at,
    intentId: row.intentId ?? row.intent_id,
    previewOnly: row.previewOnly ?? row.preview_only ?? true,
    canSubmit: Boolean(row.canSubmit ?? row.can_submit ?? false),
    latestPrice: Number(row.latestPrice ?? row.latest_price ?? price),
    estimatedAmount: Number(row.estimatedAmount ?? row.estimated_amount ?? amount),
    sourcePath: row.sourcePath ?? row.source_path,
  };
}

export function getTargetHoldings() {
  return apiOrMock('/execution/holdings', holdings);
}

export async function getOrderList() {
  const rows = await apiOrMock('/execution/orders', orders);
  return rows.map(normalizeOrder);
}

export function getTradeList() {
  return apiOrMock('/execution/trades', trades);
}

export function previewOrderAction(orderId: string) {
  return postMockAction('/actions/order-preview', { orderId });
}
