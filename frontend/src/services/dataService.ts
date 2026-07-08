import { dataQuality, dataSources, dataTasks } from '../mock/mockData';
import { apiOrMock } from './apiClient';
import { mapDataQualityRows, mapDataSources, mapDataTasks } from './mappers';

export interface DataCleaningOverview {
  status: string;
  datasetCount: number;
  passedCount: number;
  failedCount: number;
  warningCount: number;
  recordCount: number;
  symbolCount: number;
  issueCount?: number;
  errorCount?: number;
  warningIssueCount?: number;
  cleanedFileCount?: number;
  sourcePath?: string;
}

export interface DataCleaningIssue {
  id: string;
  dataset: string;
  symbol: string;
  time: string;
  level: string;
  type: string;
  message: string;
  sourcePath?: string;
}

export interface DataCleaningRun {
  runId: string;
  name: string;
  mode: string;
  status: string;
  startedAt: string;
  finishedAt: string;
  datasetCount: number;
  recordCount: number;
  issueCount: number;
  cleanedFileCount: number;
  sourcePath?: string;
}

export interface DataCleaningStatus {
  overview: DataCleaningOverview;
  rows: any[];
  issues: DataCleaningIssue[];
  runs: DataCleaningRun[];
  updatedAt: string;
}

const cleaningFallback: DataCleaningStatus = {
  overview: { status: 'NO_DATA', datasetCount: 0, passedCount: 0, failedCount: 0, warningCount: 0, recordCount: 0, symbolCount: 0, issueCount: 0 },
  rows: [],
  issues: [],
  runs: [],
  updatedAt: '',
};

export function getDataSources() {
  return apiOrMock('/data/sources', dataSources, (body) => mapDataSources(body.data, dataSources));
}

export function getDataQualityRows() {
  return apiOrMock('/data/quality', dataQuality, (body) => mapDataQualityRows(body.data, dataQuality));
}

export function getDataTasks() {
  return apiOrMock('/data/tasks', dataTasks, (body) => mapDataTasks(body.data, dataTasks));
}

export function getDataCleaningStatus() {
  return apiOrMock('/data/cleaning/status', cleaningFallback);
}

export function getDataCleaningIssues() {
  return apiOrMock('/data/cleaning/issues', [] as DataCleaningIssue[]);
}

export function getDataCleaningRuns() {
  return apiOrMock('/data/cleaning/runs', [] as DataCleaningRun[]);
}

export async function runDataCleaning(mode = 'full_pipeline') {
  const response = await fetch('/api/v1/frontend/data/cleaning/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || data.message || '数据清洗失败');
  return data.data as DataCleaningStatus;
}
