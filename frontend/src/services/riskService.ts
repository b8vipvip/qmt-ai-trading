import { riskEvents, riskOverview, riskRules } from '../mock/mockData';
import type { RiskEvent, RiskLevel, RiskRule } from '../types';
import { apiOrMock, postMockAction } from './apiClient';

function riskLevel(value: unknown): RiskLevel {
  const text = String(value ?? '').toUpperCase();
  if (text.includes('CRITICAL')) return 'CRITICAL';
  if (text.includes('HIGH') || text.includes('BLOCK')) return 'HIGH';
  if (text.includes('MEDIUM') || text.includes('WARN')) return 'MEDIUM';
  return 'LOW';
}

function normalizeRule(row: any): RiskRule {
  return {
    id: String(row.id ?? row.rule_id ?? row.name ?? ''),
    name: String(row.name ?? row.rule_name ?? ''),
    type: (row.type ?? row.rule_type ?? '交易前') as RiskRule['type'],
    threshold: String(row.threshold ?? row.limit ?? ''),
    current: String(row.current ?? row.current_value ?? ''),
    action: (row.action ?? '拦截') as RiskRule['action'],
    enabled: Boolean(row.enabled ?? true),
    lastTriggered: String(row.lastTriggered ?? row.last_triggered ?? ''),
    description: row.description,
    sourcePath: row.sourcePath ?? row.source_path,
  };
}

function normalizeEvent(row: any): RiskEvent {
  return {
    id: String(row.id ?? row.intent_id ?? row.event_id ?? ''),
    time: String(row.time ?? row.created_at ?? ''),
    strategy: String(row.strategy ?? row.intent_id ?? ''),
    rule: String(row.rule ?? row.rule_name ?? 'Risk Gate'),
    level: riskLevel(row.level ?? row.risk_level ?? row.decision),
    trigger: String(row.trigger ?? row.trigger_value ?? row.decision ?? ''),
    threshold: String(row.threshold ?? 'safety_policy'),
    action: String(row.action ?? row.decision ?? ''),
    result: String(row.result ?? row.decision ?? ''),
    operator: String(row.operator ?? 'system'),
    sourcePath: row.sourcePath ?? row.source_path,
  };
}

export function getRiskOverview() {
  return apiOrMock('/risk/overview', riskOverview);
}

export async function getRiskRules() {
  const rows = await apiOrMock('/risk/rules', riskRules);
  return rows.map(normalizeRule);
}

export async function getRiskEvents() {
  const rows = await apiOrMock('/risk/events', riskEvents);
  return rows.map(normalizeEvent);
}

export function executeDangerActionMock(action: string) {
  return postMockAction('/actions/risk', { action });
}
