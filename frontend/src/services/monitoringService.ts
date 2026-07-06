import { equityCurve, holdings, orders, strategies, systemEvents, trades } from '../mock/mockData';
import { apiOrMock } from './apiClient';
import { mapEquityCurve, mapHoldingRows, mapOrderRows, mapSystemEvents } from './mappers';

export function getRealtimeMonitoring() {
  const fallback = {
    curve: equityCurve.slice(-60),
    holdings: holdings.slice(0, 12),
    orders: orders.slice(0, 8),
    signals: strategies.map((s) => ({ strategy: s.name, signals: s.signalCount })),
    latency: { market: '126ms', api: '88ms', db: '32ms' },
  };
  return apiOrMock('/monitoring/realtime', fallback, (body) => {
    const data = body.data || {};
    return {
      curve: mapEquityCurve(data.curve, fallback.curve),
      holdings: mapHoldingRows(data.holdings, fallback.holdings),
      orders: mapOrderRows(data.orders, fallback.orders),
      signals: data.signals || fallback.signals,
      latency: data.latency || fallback.latency,
    };
  });
}

export function getAttribution() {
  return apiOrMock('/monitoring/attribution', [{ name: '策略贡献', value: 42 }, { name: '行业贡献', value: 18 }, { name: '因子贡献', value: 25 }, { name: '择时贡献', value: 9 }, { name: '交易成本影响', value: -6 }]);
}

export function getExecutionQuality() {
  return apiOrMock('/monitoring/execution-quality', { avgSlippage: '3.6bp', fillRate: '92.4%', cancelRate: '8.1%', partialFillRate: '6.3%', latency: '410ms', impactCost: '5.2bp' });
}

export function getDailyReview() {
  const fallback = { events: systemEvents.slice(0, 10), trades: trades.slice(0, 8), summary: '今日策略组合小幅跑赢基准，风控拦截 2 条异常订单，明日关注行业暴露上限。' };
  return apiOrMock('/monitoring/daily-review', fallback, (body) => {
    const data = body.data || {};
    return {
      events: mapSystemEvents(data.events, fallback.events),
      trades: data.trades || fallback.trades,
      summary: data.summary || fallback.summary,
    };
  });
}
