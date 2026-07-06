import { equityCurve, metrics, riskOverview, strategies, systemEvents } from '../mock/mockData';
import { apiOrMock } from './apiClient';
import { mapDashboardOverview, mapEquityCurve, mapRiskOverview, mapStrategyStatusList, mapSystemEvents } from './mappers';

export function getDashboardOverview() {
  return apiOrMock('/dashboard/overview', { metrics, riskOverview }, (body) => mapDashboardOverview(body.data, { metrics, riskOverview }));
}

export function getStrategyStatusList() {
  return apiOrMock('/dashboard/strategies', strategies, (body) => mapStrategyStatusList(body.data, strategies));
}

export function getEquityCurve() {
  return apiOrMock('/dashboard/equity-curve', equityCurve, (body) => mapEquityCurve(body.data, equityCurve));
}

export function getRiskOverview() {
  return apiOrMock('/risk/overview', riskOverview, (body) => mapRiskOverview(body.data, riskOverview));
}

export function getSystemEvents() {
  return apiOrMock('/dashboard/events', systemEvents, (body) => mapSystemEvents(body.data, systemEvents));
}
