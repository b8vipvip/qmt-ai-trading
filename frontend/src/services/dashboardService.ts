import { equityCurve, metrics, riskOverview, strategies, systemEvents } from '../mock/mockData';
import { apiOrMock } from './apiClient';

export function getDashboardOverview() {
  return apiOrMock('/dashboard/overview', { metrics, riskOverview });
}

export function getStrategyStatusList() {
  return apiOrMock('/dashboard/strategies', strategies);
}

export function getEquityCurve() {
  return apiOrMock('/dashboard/equity-curve', equityCurve);
}

export function getRiskOverview() {
  return apiOrMock('/risk/overview', riskOverview);
}

export function getSystemEvents() {
  return apiOrMock('/dashboard/events', systemEvents);
}
