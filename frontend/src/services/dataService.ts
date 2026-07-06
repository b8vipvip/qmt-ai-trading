import { dataQuality, dataSources, dataTasks } from '../mock/mockData';
import { apiOrMock } from './apiClient';
import { mapDataQualityRows, mapDataSources, mapDataTasks } from './mappers';

export function getDataSources() {
  return apiOrMock('/data/sources', dataSources, (body) => mapDataSources(body.data, dataSources));
}

export function getDataQualityRows() {
  return apiOrMock('/data/quality', dataQuality, (body) => mapDataQualityRows(body.data, dataQuality));
}

export function getDataTasks() {
  return apiOrMock('/data/tasks', dataTasks, (body) => mapDataTasks(body.data, dataTasks));
}
