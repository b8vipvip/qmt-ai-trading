import { riskEvents, riskOverview, riskRules } from '../mock/mockData';
import { apiOrMock, postMockAction } from './apiClient';

export function getRiskOverview() {
  return apiOrMock('/risk/overview', riskOverview);
}

export function getRiskRules() {
  return apiOrMock('/risk/rules', riskRules);
}

export function getRiskEvents() {
  return apiOrMock('/risk/events', riskEvents);
}

export function executeDangerActionMock(action: string) {
  return postMockAction('/actions/risk', { action });
}
