import { systemEvents } from '../mock/mockData';
const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
export async function getSystemStatus() { await wait(); return { tradeDate: '2026-07-05', marketStatus: '非交易日', quote: 'normal', broker: 'offline', database: 'normal', risk: 'warning', mode: '研究' }; }
export async function getSystemEvents() { await wait(); return systemEvents; }
export async function getApiStatus() { await wait(); return ['行情 API','QMT / 券商 API','数据库','Redis','任务调度器','AI 服务','文件存储'].map((name, i) => ({ name, status: i === 1 ? 'offline' : i === 4 ? 'warning' : 'normal', latency: i === 1 ? '-' : `${20 + i * 18}ms` })); }
export async function getAuditLogs() { await wait(); return systemEvents.map((e, i) => ({ time: e.time, user: i % 2 ? 'system' : 'operator', module: e.module, action: e.message, ip: '127.0.0.1', result: e.level === 'danger' ? 'WARN' : 'OK' })); }
