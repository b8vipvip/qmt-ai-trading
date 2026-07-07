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
  sourcePath?: string;
}

export interface MarketSummary {
  quoteCount: number;
  symbolCount: number;
  upCount: number;
  downCount: number;
  flatCount: number;
  latestTime: string;
  sourcePath?: string;
}

export interface MarketAIAnalysis {
  status: string;
  modelName: string;
  apiName: string;
  generatedAt: string;
  report: string;
}

export function getMarketQuotes() {
  return apiOrMock('/data/market-quotes', [] as MarketQuoteRow[]);
}

export function getMarketSummary() {
  return apiOrMock('/data/market-summary', { quoteCount: 0, symbolCount: 0, upCount: 0, downCount: 0, flatCount: 0, latestTime: '' } as MarketSummary);
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
