import { holdings, orders, trades } from '../mock/mockData';
const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
export async function getTargetHoldings() { await wait(); return holdings; }
export async function getOrderList() { await wait(); return orders; }
export async function getTradeList() { await wait(); return trades; }
export async function previewOrderAction(orderId: string) { await wait(240); return { ok: true, orderId, dryRun: true, message: '当前仅模拟操作，没有连接交易接口。' }; }
