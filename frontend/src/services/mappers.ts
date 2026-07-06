import type { MetricItem, RiskOverview, OrderItem, StrategyItem } from '../types/console';

export function mapMetrics(data: any): MetricItem[] {
  return (data?.metrics || []).map((m: any) => ({
    title: m.title,
    value: m.value,
    change: m.change,
    status: m.status,
    trend: m.trend || [],
  }));
}

export function mapRisk(data: any): RiskOverview {
  return data?.riskOverview || data || {};
}

export function mapOrders(data: any): OrderItem[] {
  return (data || []).map((o: any) => ({
    id: o.id,
    code: o.code,
    side: o.side,
    quantity: o.quantity,
    price: o.price,
    status: o.status,
  }));
}

export function mapStrategies(data: any): StrategyItem[] {
  return (data || []).map((s: any) => ({
    id: s.id,
    name: s.name,
    status: s.status,
  }));
}
