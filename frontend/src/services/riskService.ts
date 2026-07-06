import { riskEvents, riskOverview, riskRules } from '../mock/mockData';
const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
export async function getRiskOverview() { await wait(); return riskOverview; }
export async function getRiskRules() { await wait(); return riskRules; }
export async function getRiskEvents() { await wait(); return riskEvents; }
export async function executeDangerActionMock(action: string) { await wait(240); return { ok: true, action, dryRun: true, message: '危险操作只完成 UI 保护验证，未连接实盘接口。' }; }
