import { riskEvents, riskOverview, riskRules } from '../mock/mockData';
import { apiOrMock, postMockAction } from './apiClient';
import { mapRiskEvents, mapRiskOverview, mapRiskRules } from './mappers';

export function getRiskOverview() {
  return apiOrMock('/risk/overview', riskOverview, (body) => mapRiskOverview(body.data, riskOverview));
}

export function getRiskRules() {
  return apiOrMock('/risk/rules', riskRules, (body) => mapRiskRules(body.data, riskRules));
}

export function getRiskEvents() {
  return apiOrMock('/risk/events', riskEvents, (body) => mapRiskEvents(body.data, riskEvents));
}

export function executeDangerActionMock(action: string) {
  return postMockAction('/actions/risk', { action });
}
