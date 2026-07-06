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

export function getMarketQuotes() {
  return apiOrMock('/data/market-quotes', [] as MarketQuoteRow[]);
}

export function getMarketSummary() {
  return apiOrMock('/data/market-summary', { quoteCount: 0, symbolCount: 0, upCount: 0, downCount: 0, flatCount: 0, latestTime: '' } as MarketSummary);
}
