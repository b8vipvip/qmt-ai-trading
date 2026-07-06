import { dataQuality, dataSources, dataTasks } from '../mock/mockData';
import { apiOrMock } from './apiClient';

export function getDataSources() {
  return apiOrMock('/data/sources', dataSources);
}

export function getDataQualityRows() {
  return apiOrMock('/data/quality', dataQuality);
}

export function getDataTasks() {
  return apiOrMock('/data/tasks', dataTasks);
}
