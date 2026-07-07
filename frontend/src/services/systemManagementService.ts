import { apiOrMock } from './apiClient';

export interface ConfigRow { key: string; name: string; value: string; source: string; editable: boolean; sensitive: boolean }
export interface ApiRow { name: string; endpoint: string; status: string; method: string; source: string }
export interface AuditRow { time: string; user: string; module: string; operation: string; paramsSummary: string; ip: string; result: string; runId?: string; sourcePath?: string }
export interface PermissionRow { id: string; name: string; category: string; safeMode: boolean; dryRunOnly: boolean; requiresHumanApproval: boolean; forbiddenInLive: boolean; commandAdapter: string; outputArtifacts: string[]; canRunFromFrontend: boolean; sourcePath?: string }
export interface SystemSummary { artifactRoot: string; taskCount: number; historyCount: number; apiConfigCount: number; enabledApiConfigCount: number; latestRunAt: string; runMode: string; qmtPathConfigured?: boolean; liveTradingEnabled: boolean; orderSubmitEnabled: boolean; orderCancelEnabled: boolean; sourcePath?: string }
export interface SystemSettings {
  runtime: { mode: string };
  qmt: { qmtClientPath: string; xtdataPath: string; xtquantPythonPath: string; clientName: string };
  trading: { defaultStockPool: string; commissionRate: number; slippageBps: number; rebalancePeriod: string; backtestInitialCash: number; backtestStartDate: string; backtestEndDate: string; stampTaxRate: number; enableT1: boolean; enableLimitCheck: boolean; enableSuspensionCheck: boolean; enableLiquidityLimit: boolean };
  risk: { maxPositionPct: number; maxSinglePositionPct: number; maxIndustryExposurePct: number; maxDrawdownPct: number; dailyLossLimitPct: number };
  paths: { marketCacheDir: string; factorArtifactDir: string; backtestReportDir: string; taskHistoryDir: string };
  safety: { allowRealOrder: boolean; allowCancelOrder: boolean; allowAccountQuery: boolean; enableHumanApproval: boolean };
}
export interface ApiConfigRow { id: string; name: string; provider: string; baseUrl: string; account: string; modelName: string; enabled: boolean; note: string; updatedAt: string; purposes: string[]; hasToken: boolean; tokenMasked: string; sourcePath?: string }
export interface ApiConfigTestResult { id: string; provider: string; purposes: string[]; enabled: boolean; checkedAt: string; status: string; message: string; sourcePath?: string }
export interface QmtPathCheck { kind: string; label: string; path: string; status: string; message: string }
export interface QmtTestResult { kind: string; checks: QmtPathCheck[]; checkedAt: string; status: string; message: string; sourcePath?: string }
export interface QmtPathCandidate { path: string; kind: string; label: string; exists: boolean; clientName: string }
export interface QmtScanResult { target: string; current: SystemSettings['qmt']; candidates: QmtPathCandidate[]; count: number; note: string }

export const settingsFallback: SystemSettings = {
  runtime: { mode: 'research' },
  qmt: { qmtClientPath: '', xtdataPath: '', xtquantPythonPath: '', clientName: 'QMT' },
  trading: { defaultStockPool: '沪深300', commissionRate: 0.00025, slippageBps: 3, rebalancePeriod: 'daily', backtestInitialCash: 1000000, backtestStartDate: '2021-01-01', backtestEndDate: '', stampTaxRate: 0.001, enableT1: true, enableLimitCheck: true, enableSuspensionCheck: true, enableLiquidityLimit: true },
  risk: { maxPositionPct: 80, maxSinglePositionPct: 10, maxIndustryExposurePct: 30, maxDrawdownPct: 15, dailyLossLimitPct: 3 },
  paths: { marketCacheDir: 'artifacts/reports/console/datahub', factorArtifactDir: 'artifacts/reports/console/research', backtestReportDir: 'artifacts/reports/console/backtest', taskHistoryDir: 'artifacts/reports/console/task_history' },
  safety: { allowRealOrder: false, allowCancelOrder: false, allowAccountQuery: false, enableHumanApproval: true },
};

export function getSystemConfigRows() { return apiOrMock('/system/config', [] as ConfigRow[]); }
export function getSystemSettings() { return apiOrMock('/system/settings', settingsFallback); }
export function getSystemApiRows() { return apiOrMock('/system/api-status', [] as ApiRow[]); }
export function getSystemAuditRows() { return apiOrMock('/system/audit-logs', [] as AuditRow[]); }
export function getSystemPermissionRows() { return apiOrMock('/system/permissions', [] as PermissionRow[]); }
export function getSystemSummary() { return apiOrMock('/system/summary', { artifactRoot: '', taskCount: 0, historyCount: 0, apiConfigCount: 0, enabledApiConfigCount: 0, latestRunAt: '', runMode: 'research', qmtPathConfigured: false, liveTradingEnabled: false, orderSubmitEnabled: false, orderCancelEnabled: false } as SystemSummary); }
export function getApiConfigs() { return apiOrMock('/system/api-configs', [] as ApiConfigRow[]); }

export async function saveSystemSettings(settings: SystemSettings) {
  const response = await fetch('/api/v1/frontend/system/settings/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ settings }) });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || '保存系统配置失败');
  return data.data as SystemSettings;
}

export async function scanQmtPaths(target: 'all' | 'qmtClientPath' | 'xtdataPath' | 'xtquantPythonPath' = 'all') {
  const response = await fetch('/api/v1/frontend/system/qmt/scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target }) });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || '扫描 QMT / xtdata 路径失败');
  return data.data as QmtScanResult;
}

export async function testQmtSettings(kind: 'all' | 'qmtClientPath' | 'xtdataPath' | 'xtquantPythonPath' = 'all') {
  const response = await fetch('/api/v1/frontend/system/qmt/test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ kind }) });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || '测试 QMT / xtdata 配置失败');
  return data.data as QmtTestResult;
}

export async function saveApiConfig(config: Partial<ApiConfigRow> & { token?: string }) {
  const response = await fetch('/api/v1/frontend/system/api-configs/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ config }) });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || '保存 API 配置失败');
  return data.data as ApiConfigRow;
}

export async function saveApiConfigPurposes(id: string, purposes: string[]) {
  const response = await fetch('/api/v1/frontend/system/api-configs/purposes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id, purposes }) });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || '保存 API 用途失败');
  return data.data as ApiConfigRow;
}

export async function testApiConfig(id: string) {
  const response = await fetch('/api/v1/frontend/system/api-configs/test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || '测试 API 配置失败');
  return data.data as ApiConfigTestResult;
}
