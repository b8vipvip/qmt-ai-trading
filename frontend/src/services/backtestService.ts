import { backtestTasks, equityCurve, holdings, orders } from '../mock/mockData';
const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
export async function getBacktestTasks() { await wait(); return backtestTasks; }
export async function getBacktestReport(id?: string) { await wait(); return { task: backtestTasks.find((item) => item.id === id) ?? backtestTasks[0], curve: equityCurve, metrics: { annualReturn: 18.6, maxDrawdown: -7.8, sharpe: 1.62, calmar: 2.38, winRate: 58.4, profitLossRatio: 1.31, turnover: 3.8, trades: 286, excessReturn: 11.2 }, positions: holdings.slice(0, 12), trades: orders.slice(0, 12) }; }
