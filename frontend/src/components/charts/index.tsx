import ReactECharts from 'echarts-for-react';
import type { EquityPoint } from '../../types';

export function EquityCurveChart({ data }: { data: EquityPoint[] }) {
  return <ReactECharts className="chart" option={{ tooltip: { trigger: 'axis' }, legend: { textStyle: { color: '#94a3b8' }, data: ['账户权益', '沪深300基准', '回撤'] }, grid: { left: 46, right: 28, top: 44, bottom: 30 }, xAxis: { type: 'category', data: data.map((d) => d.date), axisLabel: { color: '#94a3b8' } }, yAxis: [{ type: 'value', axisLabel: { color: '#94a3b8' } }, { type: 'value', axisLabel: { color: '#94a3b8', formatter: '{value}%' } }], series: [{ name: '账户权益', type: 'line', smooth: true, symbol: 'none', data: data.map((d) => d.equity) }, { name: '沪深300基准', type: 'line', smooth: true, symbol: 'none', data: data.map((d) => d.benchmark) }, { name: '回撤', type: 'line', yAxisIndex: 1, areaStyle: {}, smooth: true, symbol: 'none', data: data.map((d) => d.drawdown) }] }} />;
}

export function DrawdownChart({ data }: { data: EquityPoint[] }) {
  return <ReactECharts className="chart small" option={{ tooltip: { trigger: 'axis' }, grid: { left: 42, right: 20, top: 20, bottom: 26 }, xAxis: { type: 'category', data: data.map((d) => d.date), axisLabel: { color: '#94a3b8' } }, yAxis: { type: 'value', axisLabel: { color: '#94a3b8', formatter: '{value}%' } }, series: [{ name: '回撤', type: 'bar', data: data.map((d) => d.drawdown) }] }} />;
}

export function BarChart({ names, values, title }: { names: string[]; values: number[]; title?: string }) {
  return <ReactECharts className="chart small" option={{ title: { text: title, textStyle: { color: '#cbd5e1', fontSize: 13 } }, tooltip: {}, grid: { left: 42, right: 16, top: 38, bottom: 28 }, xAxis: { type: 'category', data: names, axisLabel: { color: '#94a3b8' } }, yAxis: { type: 'value', axisLabel: { color: '#94a3b8' } }, series: [{ type: 'bar', data: values }] }} />;
}
