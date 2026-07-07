import { Alert, Button, Card, Col, message, Row, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { EmptyState } from '../components/common';
import { getDataQualityRows, getDataSources } from '../services/dataService';
import { getMarketQuotes, getMarketSummary, runMarketAIAnalysis } from '../services/marketDataService';
import type { MarketAIAnalysis, MarketQuoteRow, MarketSummary } from '../services/marketDataService';
import { runConsoleTask } from '../services/taskService';
import type { DataQualityRow, DataSourceStatus } from '../types';

function useAsync<T>(loader: () => Promise<T>, fallback: T): T {
  const [data, setData] = useState<T>(fallback);
  useEffect(() => {
    let mounted = true;
    const load = () => loader().then((v) => { if (mounted) setData(v); }).catch(() => { if (mounted) setData(fallback); });
    load();
    window.addEventListener('qmt-task-finished', load);
    window.addEventListener('qmt-api-config-saved', load);
    return () => { mounted = false; window.removeEventListener('qmt-task-finished', load); window.removeEventListener('qmt-api-config-saved', load); };
  }, []);
  return data;
}

function Section({ title, extra, children }: { title: string; extra?: ReactNode; children: ReactNode }) {
  return <Card className="section-card" title={title} extra={extra}>{children}</Card>;
}

function TaskButton({ taskId, params, children, type }: { taskId: string; params?: Record<string, unknown>; children: ReactNode; type?: 'primary' | 'default' }) {
  const [running, setRunning] = useState(false);
  const run = async () => {
    try {
      setRunning(true);
      const res = await runConsoleTask({ taskId, params });
      message.success(`${res.task?.task_name || taskId} ${res.task?.status || 'DONE'}`);
      window.dispatchEvent(new Event('qmt-task-finished'));
    } catch (error) {
      message.error(error instanceof Error ? error.message : String(error));
    } finally {
      setRunning(false);
    }
  };
  return <Button size="small" type={type} loading={running} onClick={run}>{children}</Button>;
}

function price(value: number) {
  return Number(value || 0).toFixed(3);
}

function money(value: number) {
  const n = Number(value || 0);
  return n ? `¥${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '-';
}

function statusTag(value: string) {
  const text = String(value || 'UNKNOWN');
  return <Tag color={text === 'NORMAL' || text === 'READY' ? 'green' : text === 'PENDING' ? 'gold' : 'default'}>{text}</Tag>;
}

function dataModeTag(summary: MarketSummary) {
  if (summary.realMarketData) return <Tag color="green">真实 xtdata</Tag>;
  if (summary.sandboxFallback || summary.dataMode === 'SANDBOX_FALLBACK') return <Tag color="gold">沙盒样例</Tag>;
  return <Tag>未知</Tag>;
}

function AnalysisReport({ report, error }: { report?: MarketAIAnalysis; error?: string }) {
  if (error) {
    return <Alert type="error" showIcon message="AI 行情分析失败" description={error} />;
  }
  if (!report) {
    return <EmptyState text="尚未生成 AI 行情分析；点击“行情数据任务”里的“AI 分析行情”后会在这里输出报告。" />;
  }
  return <Space direction="vertical" style={{ width: '100%' }} size={12}>
    <Alert type="success" showIcon message="AI 行情分析完成" description={`模型：${report.modelName || report.apiName || '-'}；生成时间：${report.generatedAt || '-'}`} />
    <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, margin: 0 }}>{report.report}</Typography.Paragraph>
  </Space>;
}

export function MarketDataPage() {
  const sources = useAsync(getDataSources, [] as DataSourceStatus[]);
  const quality = useAsync(getDataQualityRows, [] as DataQualityRow[]);
  const quotes = useAsync(getMarketQuotes, [] as MarketQuoteRow[]);
  const summary = useAsync(getMarketSummary, { quoteCount: 0, symbolCount: 0, upCount: 0, downCount: 0, flatCount: 0, latestTime: '', realMarketData: false, sandboxFallback: true, dataMode: 'UNKNOWN' } as MarketSummary);
  const [analysis, setAnalysis] = useState<MarketAIAnalysis | undefined>();
  const [analysisError, setAnalysisError] = useState<string>('');
  const [analyzing, setAnalyzing] = useState(false);

  const analyze = async () => {
    try {
      setAnalyzing(true);
      setAnalysisError('');
      const res = await runMarketAIAnalysis();
      setAnalysis(res);
      message.success('AI 行情分析完成');
    } catch (error) {
      const text = error instanceof Error ? error.message : String(error);
      setAnalysisError(text);
      message.error(text);
    } finally {
      setAnalyzing(false);
    }
  };

  const columns: ColumnsType<MarketQuoteRow> = [
    { title: '代码', dataIndex: 'symbol', fixed: 'left', width: 130 },
    { title: '名称', dataIndex: 'name', width: 130 },
    { title: '时间', dataIndex: 'time', width: 180 },
    { title: '最新价', dataIndex: 'latest', width: 100, render: price },
    { title: '涨跌', dataIndex: 'change', width: 100, render: (v) => <span className={Number(v) >= 0 ? 'up' : 'down'}>{price(v)}</span> },
    { title: '涨跌幅', dataIndex: 'changePct', width: 100, render: (v) => <span className={Number(v) >= 0 ? 'up' : 'down'}>{price(v)}%</span> },
    { title: '开盘', dataIndex: 'open', width: 90, render: price },
    { title: '最高', dataIndex: 'high', width: 90, render: price },
    { title: '最低', dataIndex: 'low', width: 90, render: price },
    { title: '收盘', dataIndex: 'close', width: 90, render: price },
    { title: '成交量', dataIndex: 'volume', width: 120, render: (v) => Number(v || 0).toLocaleString() },
    { title: '成交额', dataIndex: 'amount', width: 120, render: money },
    { title: '状态', dataIndex: 'status', width: 100, render: statusTag },
  ];

  return <div className="page-grid">
    <Section title="行情数据用途">
      <Typography.Paragraph>
        行情数据是量化系统的“价格与成交事实层”，用于生成 K 线、计算收益率和波动率、更新因子、触发策略信号、估算成交成本、校验停牌/涨跌停/流动性，并为回测、仿真、影子实盘和风控提供统一输入。
      </Typography.Paragraph>
      <Space wrap>
        <Tag color="cyan">采集：xtdata / 本地缓存 / 外部数据源</Tag>
        <Tag color="green">清洗：复权 / 对齐 / 去异常 / 去重复</Tag>
        <Tag color="gold">校验：延迟 / 缺失 / 异常 / 覆盖率</Tag>
        <Tag color="purple">服务：因子研究 / 策略信号 / 风控 / 监控复盘</Tag>
      </Space>
    </Section>

    <Section title="行情数据任务" extra={<Tag color="green">只读 / dry-run / 不触发交易</Tag>}>
      <Space wrap>
        <TaskButton taskId="xtdata_live_readonly_smoke" type="primary">真实 xtdata 只读 smoke</TaskButton>
        <TaskButton taskId="qmt_data_diagnostics_readonly">QMT 行情只读诊断</TaskButton>
        <TaskButton taskId="market_snapshot_readonly">只读行情快照</TaskButton>
        <TaskButton taskId="data_cache_check">本地缓存质量检查</TaskButton>
        <Button size="small" type="primary" loading={analyzing} onClick={analyze}>AI 分析行情</Button>
      </Space>
    </Section>

    <Row gutter={[16, 16]}>
      <Col xs={24} md={8}><Card className="metric-card"><b>行情记录数</b><div className="metric-value">{summary.quoteCount}</div><span>当前快照记录数量</span></Card></Col>
      <Col xs={24} md={8}><Card className="metric-card"><b>统一标的数</b><div className="metric-value">{summary.symbolCount}</div><span>上涨 {summary.upCount} / 下跌 {summary.downCount} / 平盘 {summary.flatCount}</span></Card></Col>
      <Col xs={24} md={8}><Card className="metric-card"><b>最新时间</b><div className="metric-value" style={{ fontSize: 18 }}>{summary.latestTime || '-'}</div><Space wrap>{dataModeTag(summary)}<span>{summary.sandboxFallback ? '当前为沙盒样例时间，不是真实市场时间' : '用于判断行情是否滞后'}</span></Space></Card></Col>
    </Row>

    <Section title="AI 行情分析报告">
      <AnalysisReport report={analysis} error={analysisError} />
    </Section>

    <Section title="数据源状态">
      <Row gutter={[16, 16]}>{sources.map((s) => <Col xs={24} sm={12} lg={6} key={s.name}><Card className="source-card"><Space direction="vertical"><Space><b>{s.name}</b>{statusTag(String(s.status))}</Space><span>更新时间：{s.updatedAt || '-'}</span><span>今日记录：{Number(s.records || 0).toLocaleString()}</span><span>延迟：{s.latency}</span><span>质量：{s.qualityLevel || '-'}</span><span>缺失/异常：{s.missingRate}% / {s.abnormalRate}%</span><TaskButton taskId={s.name.includes('QMT') ? 'xtdata_live_readonly_smoke' : 'market_snapshot_readonly'}>刷新</TaskButton></Space></Card></Col>)}</Row>
    </Section>

    <Section title="行情明细表" extra={<TaskButton taskId="xtdata_live_readonly_smoke">刷新行情</TaskButton>}>
      <Table rowKey="id" size="small" dataSource={quotes} columns={columns} scroll={{ x: 1380, y: 420 }} locale={{ emptyText: <EmptyState text="暂无行情明细；点击上方真实 xtdata 只读 smoke 或只读行情快照后刷新。" /> }} />
    </Section>

    <Section title="行情数据质量">
      <Table rowKey="dataset" size="small" dataSource={quality} columns={[{ title:'数据集', dataIndex:'dataset' },{ title:'交易日', dataIndex:'tradeDate' },{ title:'覆盖股票数', dataIndex:'stockCount' },{ title:'缺失字段数', dataIndex:'missingFields' },{ title:'异常值数量', dataIndex:'abnormalValues' },{ title:'重复记录数', dataIndex:'duplicateRows' },{ title:'校验', dataIndex:'passed', render:(v)=> <Tag color={v?'green':'red'}>{v?'通过':'失败'}</Tag> },{ title:'操作', render:()=> <Space><TaskButton taskId="qmt_data_diagnostics_readonly">诊断</TaskButton><TaskButton taskId="data_cache_check">检查缓存</TaskButton></Space> }]} scroll={{ x: 950 }} locale={{ emptyText: <EmptyState text="暂无行情质量产物；运行行情任务后自动生成。" /> }} />
    </Section>
  </div>;
}
