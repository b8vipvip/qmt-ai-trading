import { apiOrMock } from './apiClient';

export interface MarketQuoteRow {
  id: string;
  symbol: string;
  name: string;
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  latest: number;
  preClose: number;
  change: number;
  changePct: number;
  volume: number;
  amount: number;
  status: string;
  source: string;
  realMarketData?: boolean;
  sandboxFallback?: boolean;
  sourcePath?: string;
}

export interface MarketSummary {
  quoteCount: number;
  symbolCount: number;
  upCount: number;
  downCount: number;
  flatCount: number;
  latestTime: string;
  realMarketData?: boolean;
  sandboxFallback?: boolean;
  dataMode?: string;
  sourcePath?: string;
}

export interface MarketAIAnalysis {
  status: string;
  modelName: string;
  apiName: string;
  generatedAt: string;
  report: string;
}

export interface MarketAutoRefreshStatus {
  enabled: boolean;
  intervalSec: number;
  onlyMissingCache: boolean;
  running: boolean;
  threadAlive: boolean;
  lastRunAt: string;
  lastStatus: string;
  lastMessage: string;
  lastRealMarketData: boolean;
  lastSandboxFallback: boolean;
  lastFailureReason: string;
  runCount: number;
  sourcePath?: string;
}

const autoFallback: MarketAutoRefreshStatus = {
  enabled: false,
  intervalSec: 60,
  onlyMissingCache: true,
  running: false,
  threadAlive: false,
  lastRunAt: '',
  lastStatus: 'IDLE',
  lastMessage: '自动刷新未启动',
  lastRealMarketData: false,
  lastSandboxFallback: false,
  lastFailureReason: '',
  runCount: 0,
};

export function getMarketQuotes() {
  return apiOrMock('/data/market-quotes', [] as MarketQuoteRow[]);
}

export function getMarketSummary() {
  return apiOrMock('/data/market-summary', { quoteCount: 0, symbolCount: 0, upCount: 0, downCount: 0, flatCount: 0, latestTime: '', realMarketData: false, sandboxFallback: true, dataMode: 'UNKNOWN' } as MarketSummary);
}

export function getMarketAutoRefreshStatus() {
  return apiOrMock('/data/market-auto-refresh/status', autoFallback);
}

export async function saveMarketAutoRefresh(settings: Partial<Pick<MarketAutoRefreshStatus, 'enabled' | 'intervalSec' | 'onlyMissingCache'>>) {
  const response = await fetch('/api/v1/frontend/data/market-auto-refresh/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || data.message || '保存自动刷新行情设置失败');
  return data.data as MarketAutoRefreshStatus;
}

export async function runMarketAIAnalysis() {
  const response = await fetch('/api/v1/frontend/data/market-ai-analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || data.message || 'AI 行情分析失败');
  return data.data as MarketAIAnalysis;
}
