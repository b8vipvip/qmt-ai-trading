import { apiOrMock } from './apiClient';

export interface FundamentalSourceRow { name: string; status: string; updatedAt: string; records: number; latency: string; coverage: number; missingRate: number; sourcePath?: string }
export interface FundamentalRecordRow { symbol: string; name: string; reportDate: string; pe: number; pb: number; roe: number; revenueGrowth: number; netProfitGrowth: number; status: string; note?: string; sourcePath?: string }
export interface NewsItemRow { id: string; time: string; type: string; title: string; symbols: string; sentiment: string; impact: string; source: string; sourcePath?: string }
export interface QualityOverview { datasetCount: number; passedCount: number; failedCount: number; warningCount: number; recordCount: number; symbolCount: number; sourcePath?: string }
export interface TaskCatalogRow { task_id: string; title_zh: string; category: string; description_zh: string; safe_mode: boolean; dry_run_only: boolean; forbidden_in_live: boolean; output_artifacts: string[] }

export function getFundamentalSources() { return apiOrMock('/data/fundamental-sources', [] as FundamentalSourceRow[]); }
export function getFundamentalRecords() { return apiOrMock('/data/fundamental-records', [] as FundamentalRecordRow[]); }
export function getNewsItems() { return apiOrMock('/data/news-items', [] as NewsItemRow[]); }
export function getQualityOverview() { return apiOrMock('/data/quality-overview', { datasetCount: 0, passedCount: 0, failedCount: 0, warningCount: 0, recordCount: 0, symbolCount: 0 } as QualityOverview); }
export function getTaskCatalog() { return apiOrMock('/data/task-catalog', [] as TaskCatalogRow[]); }
