import { equityCurve, metrics, riskOverview, strategies, systemEvents } from '../mock/mockData';

const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));

export async function getDashboardOverview() { await wait(); return { metrics, riskOverview }; }
export async function getStrategyStatusList() { await wait(); return strategies; }
export async function getEquityCurve() { await wait(); return equityCurve; }
export async function getRiskOverview() { await wait(); return riskOverview; }
export async function getSystemEvents() { await wait(); return systemEvents; }
