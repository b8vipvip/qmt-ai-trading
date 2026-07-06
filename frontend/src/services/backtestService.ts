import { backtestTasks, equityCurve, holdings, orders } from '../mock/mockData';
import { apiOrMock } from './apiClient';
import { mapBacktestTasks, mapEquityCurve, mapHoldingRows, mapOrderRows } from './mappers';

export function getBacktestTasks() {
  return apiOrMock('/backtest/tasks', backtestTasks, (body) => mapBacktestTasks(body.data, backtestTasks));
}

export function getBacktestReport(id?: string) {
  const fallback = {
    task: backtestTasks.find((item) => item.id === id) ?? backtestTasks[0],
    curve: equityCurve,
    metrics: { annualReturn: 18.6, maxDrawdown: -7.8, sharpe: 1.62, calmar: 2.38, winRate: 58.4, profitLossRatio: 1.31, turnover: 3.8, trades: 286, excessReturn: 11.2 },
    positions: holdings.slice(0, 12),
    trades: orders.slice(0, 12),
  };
  return apiOrMock('/backtest/report', fallback, (body) => {
    const data = body.data || {};
    return {
      task: data.task || fallback.task,
      curve: mapEquityCurve(data.curve, fallback.curve),
      metrics: data.metrics || fallback.metrics,
      positions: mapHoldingRows(data.positions, fallback.positions),
      trades: mapOrderRows(data.trades, fallback.trades),
    };
  });
}
