import { deploymentStages } from '../mock/mockData';
import { apiOrMock } from './apiClient';

export function getDeploymentStages() {
  return apiOrMock('/deployment/stages', deploymentStages);
}
