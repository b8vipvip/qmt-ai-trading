import { holdings, orders, strategies } from '../mock/mockData';
const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
export async function getStrategyList() { await wait(); return strategies; }
export async function getStrategyDetail(id: string) { await wait(); return { strategy: strategies.find((item) => item.id === id) ?? strategies[0], holdings: holdings.slice(0, 12), rebalanceOrders: orders.slice(0, 8) }; }
export async function getRebalancePlan() { await wait(); return { holdings: holdings.slice(0, 16), orders: orders.slice(0, 10), riskPassed: false, notice: '调仓计划只进入风控闸门，不直接下单。' }; }
