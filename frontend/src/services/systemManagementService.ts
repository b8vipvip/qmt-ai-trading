import { apiOrMock } from './apiClient';

export interface ConfigRow { key: string; name: string; value: string; source: string; editable: boolean; sensitive: boolean }
export interface ApiRow { name: string; endpoint: string; status: string; method: string; source: string }
export interface AuditRow { time: string; user: string; module: string; operation: string; paramsSummary: string; ip: string; result: string; runId?: string; sourcePath?: string }
export interface PermissionRow { id: string; name: string; category: string; safeMode: boolean; dryRunOnly: boolean; requiresHumanApproval: boolean; forbiddenInLive: boolean; commandAdapter: string; outputArtifacts: string[]; canRunFromFrontend: boolean; sourcePath?: string }
export interface SystemSummary { artifactRoot: string; taskCount: number; historyCount: number; latestRunAt: string; liveTradingEnabled: boolean; orderSubmitEnabled: boolean; orderCancelEnabled: boolean; sourcePath?: string }

export function getSystemConfigRows() { return apiOrMock('/system/config', [] as ConfigRow[]); }
export function getSystemApiRows() { return apiOrMock('/system/api-status', [] as ApiRow[]); }
export function getSystemAuditRows() { return apiOrMock('/system/audit-logs', [] as AuditRow[]); }
export function getSystemPermissionRows() { return apiOrMock('/system/permissions', [] as PermissionRow[]); }
export function getSystemSummary() { return apiOrMock('/system/summary', { artifactRoot: '', taskCount: 0, historyCount: 0, latestRunAt: '', liveTradingEnabled: false, orderSubmitEnabled: false, orderCancelEnabled: false } as SystemSummary); }
