export interface MetricItem {
  title: string;
  value: string | number;
  change?: string;
  status?: string;
  trend?: number[];
}

export interface RiskOverview {
  level: string;
  triggerCount: number;
  blockedOrders: number;
  totalPosition: number;
  currentDrawdown: number;
}

export interface OrderItem {
  id: string;
  code: string;
  side: string;
  quantity: number;
  price: number;
  status: string;
}

export interface StrategyItem {
  id: string;
  name: string;
  status: string;
}
