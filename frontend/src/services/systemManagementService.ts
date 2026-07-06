import { apiOrMock } from './apiClient';

export interface ConfigRow { key: string; name: string; value: string; source: string; editable: boolean; sensitive: boolean }
export interface ApiRow { name: string; endpoint: string; status: string; method: string; source: string }
export interface AuditRow { time: string; user: string; module: string; operation: string; paramsSummary: string; ip: string; result: string; runId?: string; sourcePath?: string }
export interface PermissionRow { id: string; name: string; category: string; safeMode: boolean; dryRunOnly: boolean; requiresHumanApproval: boolean; forbiddenInLive: boolean; commandAdapter: string; outputArtifacts: string[]; canRunFromFrontend: boolean; sourcePath?: string }
export interface SystemSummary { artifactRoot: string; taskCount: number; historyCount: number; apiConfigCount: number; enabledApiConfigCount: number; latestRunAt: string; liveTradingEnabled: boolean; orderSubmitEnabled: boolean; orderCancelEnabled: boolean; sourcePath?: string }
export interface ApiConfigRow { id: string; name: string; provider: string; purpose: string; baseUrl: string; account: string; enabled: boolean; note: string; updatedAt: string; hasToken: boolean; tokenMasked: string; sourcePath?: string }
export interface ApiConfigTestResult { id: string; provider: string; purpose: string; enabled: boolean; checkedAt: string; status: string; message: string; sourcePath?: string }

export function getSystemConfigRows() { return apiOrMock('/system/config', [] as ConfigRow[]); }
export function getSystemApiRows() { return apiOrMock('/system/api-status', [] as ApiRow[]); }
export function getSystemAuditRows() { return apiOrMock('/system/audit-logs', [] as AuditRow[]); }
export function getSystemPermissionRows() { return apiOrMock('/system/permissions', [] as PermissionRow[]); }
export function getSystemSummary() { return apiOrMock('/system/summary', { artifactRoot: '', taskCount: 0, historyCount: 0, apiConfigCount: 0, enabledApiConfigCount: 0, latestRunAt: '', liveTradingEnabled: false, orderSubmitEnabled: false, orderCancelEnabled: false } as SystemSummary); }
export function getApiConfigs() { return apiOrMock('/system/api-configs', [] as ApiConfigRow[]); }

export async function saveApiConfig(config: Partial<ApiConfigRow> & { token?: string }) {
  const response = await fetch('/api/v1/frontend/system/api-configs/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ config }) });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || '保存 API 配置失败');
  return data.data as ApiConfigRow;
}

export async function testApiConfig(id: string) {
  const response = await fetch('/api/v1/frontend/system/api-configs/test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || '测试 API 配置失败');
  return data.data as ApiConfigTestResult;
}
