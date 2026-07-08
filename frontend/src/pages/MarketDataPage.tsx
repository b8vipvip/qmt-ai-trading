import { Alert, Button, Card, Col, InputNumber, message, Row, Space, Switch, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { EmptyState } from '../components/common';
import { getDataSources } from '../services/dataService';
import { getDownloadedDatasetStatus, getMarketAutoRefreshStatus, getMarketQuotes, getMarketSummary, getMarketUniverseStatus, getQmtUniverseSyncStatus, runMarketAIAnalysis, runQmtUniverseSync, saveMarketAutoRefresh, saveMarketUniverse } from '../services/marketDataService';
import type { DownloadedDatasetRow, DownloadedDatasetStatus, MarketAIAnalysis, MarketAutoRefreshStatus, MarketQuoteRow, MarketSummary, MarketUniverseStatus, QmtUniverseGroup, QmtUniverseSyncResult } from '../services/marketDataService';
import type { DataSourceStatus } from '../types';

function useAsync<T>(loader: () => Promise<T>, fallback: T): T {
  const [data, setData] = useState<T>(fallback);
  useEffect(() => {
    let mounted = true;
    const load = () => loader().then((v) => { if (mounted) setData(v); }).catch(() => { if (mounted) setData(fallback); });
    load();
    window.addEventListener('qmt-task-finished', load);
    window.addEventListener('qmt-api-config-saved', load);
    window.addEventListener('qmt-market-auto-refresh-updated', load);
    window.addEventListener('qmt-market-universe-updated', load);
    window.addEventListener('qmt-downloaded-datasets-updated', load);
    return () => { mounted = false; window.removeEventListener('qmt-task-finished', load); window.removeEventListener('qmt-api-config-saved', load); window.removeEventListener('qmt-market-auto-refresh-updated', load); window.removeEventListener('qmt-market-universe-updated', load); window.removeEventListener('qmt-downloaded-datasets-updated', load); };
  }, []);
  return data;
}

function Section({ title, extra, children }: { title: ReactNode; extra?: ReactNode; children: ReactNode }) { return <Card className="section-card" title={title} extra={extra}>{children}</Card>; }
function price(value: number) { return Number(value || 0).toFixed(3); }
function money(value: number) { const n = Number(value || 0); return n ? `¥${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '-'; }

function parseMarketTimeMs(value: unknown): number | null {
  if (value === undefined || value === null || value === '') return null;
  const raw = String(value).trim();
  if (!raw || raw.includes('*')) return null;
  const digits = raw.replace(/\.0+$/, '');
  if (/^\d{13}$/.test(digits)) return Number(digits);
  if (/^\d{10}$/.test(digits)) return Number(digits) * 1000;
  if (/^\d{14}$/.test(digits)) { const d = new Date(Number(digits.slice(0, 4)), Number(digits.slice(4, 6)) - 1, Number(digits.slice(6, 8)), Number(digits.slice(8, 10)), Number(digits.slice(10, 12)), Number(digits.slice(12, 14))); return Number.isNaN(d.getTime()) ? null : d.getTime(); }
  if (/^\d{8}$/.test(digits)) { const d = new Date(Number(digits.slice(0, 4)), Number(digits.slice(4, 6)) - 1, Number(digits.slice(6, 8))); return Number.isNaN(d.getTime()) ? null : d.getTime(); }
  const parsed = new Date(raw); return Number.isNaN(parsed.getTime()) ? null : parsed.getTime();
}
function formatMarketTime(value: unknown) {
  const ms = parseMarketTimeMs(value);
  if (ms !== null) return new Date(ms).toLocaleString('zh-CN', { hour12: false });
  if (value === undefined || value === null || value === '') return '-';
  const raw = String(value).trim(); if (!raw) return '-';
  const digits = raw.replace(/\.0+$/, '');
  if (/^\d{14}$/.test(digits)) return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)} ${digits.slice(8, 10)}:${digits.slice(10, 12)}:${digits.slice(12, 14)}`;
  if (/^\d{8}$/.test(digits)) return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
  return raw;
}
function latestMarketTime(quotes: MarketQuoteRow[], fallback: unknown) { let best: { raw: unknown; ms: number } | null = null; for (const row of quotes) { const ms = parseMarketTimeMs(row.time); if (ms !== null && (!best || ms > best.ms)) best = { raw: row.time, ms }; } return best ? formatMarketTime(best.raw) : formatMarketTime(fallback); }
function statusTag(value: string) { const text = String(value || 'UNKNOWN'); return <Tag color={text === 'NORMAL' || text === 'READY' || text === 'REAL_MARKET_DATA' ? 'green' : text === 'PENDING' || text === 'WAITING_LOGIN_OR_FALLBACK' || text === 'NOT_SYNCED' || text === 'MISSING' ? 'gold' : text === 'FAILED' ? 'red' : 'default'}>{text}</Tag>; }
function dataModeTag(summary: MarketSummary) { if (summary.realMarketData) return <Tag color="green">真实 xtdata</Tag>; if (summary.sandboxFallback || summary.dataMode === 'SANDBOX_FALLBACK') return <Tag color="gold">沙盒样例</Tag>; return <Tag>未知</Tag>; }

function AnalysisReport({ report, error }: { report?: MarketAIAnalysis; error?: string }) {
  if (error) return <Alert type="error" showIcon message="AI 行情分析失败" description={error} />;
  if (!report) return <EmptyState text="尚未生成 AI 行情分析；点击“AI 分析行情”后会在这里输出报告。" />;
  return <Space direction="vertical" style={{ width: '100%' }} size={12}><Alert type="success" showIcon message="AI 行情分析完成" description={`模型：${report.modelName || report.apiName || '-'}；生成时间：${report.generatedAt || '-'}`} /><Typography.Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, margin: 0 }}>{report.report}</Typography.Paragraph></Space>;
}

const universeFallback: MarketUniverseStatus = { preset: 'broad_etf', name: '宽基ETF池', symbols: [], symbolCount: 0, customSymbolsText: '', source: 'preset', presets: [] };
const autoFallback: MarketAutoRefreshStatus = { enabled: false, intervalSec: 60, onlyMissingCache: true, running: false, threadAlive: false, lastRunAt: '', lastStatus: 'IDLE', lastMessage: '自动刷新未启动', lastRealMarketData: false, lastSandboxFallback: false, lastFailureReason: '', runCount: 0 };
const syncFallback: QmtUniverseSyncResult = { status: 'NOT_SYNCED', syncedAt: '', message: '尚未同步 QMT 真实股票列表', groups: [], groupCount: 0 };
const downloadedFallback: DownloadedDatasetStatus = { rows: [], readyCount: 0, totalCount: 0, generatedAt: '' };

function AutoRefreshControl({ onChanged }: { onChanged: () => void }) {
  const [status, setStatus] = useState<MarketAutoRefreshStatus>(autoFallback);
  const [intervalSec, setIntervalSec] = useState(60);
  const [saving, setSaving] = useState(false);
  const load = async () => { try { const next = await getMarketAutoRefreshStatus(); setStatus(next); setIntervalSec(next.intervalSec || 60); } catch { setStatus(autoFallback); } };
  useEffect(() => { load(); const timer = window.setInterval(() => { load(); onChanged(); window.dispatchEvent(new Event('qmt-downloaded-datasets-updated')); }, 8000); return () => window.clearInterval(timer); }, []);
  const save = async (patch: Partial<Pick<MarketAutoRefreshStatus, 'enabled' | 'intervalSec' | 'onlyMissingCache'>>) => { try { setSaving(true); const next = await saveMarketAutoRefresh(patch); setStatus(next); setIntervalSec(next.intervalSec || intervalSec); message.success(next.enabled ? '自动刷新行情已开启' : '自动刷新行情已关闭'); window.dispatchEvent(new Event('qmt-market-auto-refresh-updated')); onChanged(); } catch (error) { message.error(error instanceof Error ? error.message : String(error)); } finally { setSaving(false); } };
  return <Space direction="vertical" style={{ width: '100%' }} size={12}>
    <Space wrap size={16}>
      <Switch checked={status.enabled} loading={saving} onChange={(checked) => save({ enabled: checked, intervalSec })} checkedChildren="开启" unCheckedChildren="关闭" />
      <Space><span>间隔</span><InputNumber min={10} max={3600} value={intervalSec} onChange={(value) => setIntervalSec(Number(value) || 60)} disabled={saving} /><span>秒</span><Button size="small" loading={saving} onClick={() => save({ intervalSec })}>保存</Button></Space>
      <Space><span>只下载缺失缓存</span><Switch checked={status.onlyMissingCache} loading={saving} onChange={(checked) => save({ onlyMissingCache: checked })} /></Space>
      <Tag color="blue">Universe：{status.universeName || '-'}</Tag><Tag color="cyan">标的：{status.universeSymbolCount || 0}</Tag>{statusTag(status.lastStatus)}{status.threadAlive && <Tag color="blue">后台循环中</Tag>}{status.running && <Tag color="cyan">正在检查/刷新</Tag>}
    </Space>
    <Alert type={status.lastRealMarketData ? 'success' : status.enabled ? 'warning' : 'info'} showIcon message={status.lastMessage || '自动刷新未启动'} description={`最近运行：${formatMarketTime(status.lastRunAt) || '-'}；运行次数：${status.runCount || 0}；真实行情：${status.lastRealMarketData ? '是' : '否'}；沙盒回退：${status.lastSandboxFallback ? '是' : '否'}`} />
  </Space>;
}

function QmtUniverseSyncControl({ onChanged }: { onChanged: () => void }) {
  const [sync, setSync] = useState<QmtUniverseSyncResult>(syncFallback);
  const [running, setRunning] = useState(false);
  const [applyingKey, setApplyingKey] = useState('');
  const load = async () => { try { setSync(await getQmtUniverseSyncStatus()); } catch { setSync(syncFallback); } };
  useEffect(() => { load(); }, []);
  const run = async () => {
    try { setRunning(true); const res = await runQmtUniverseSync(['all_a', 'etf', 'index', 'broad_market', 'convertible_bond', 'sector_index']); setSync(res); message.success(res.message || 'QMT 真实列表同步完成'); window.dispatchEvent(new Event('qmt-downloaded-datasets-updated')); onChanged(); }
    catch (error) { message.error(error instanceof Error ? error.message : String(error)); await load(); }
    finally { setRunning(false); }
  };
  const apply = async (group: QmtUniverseGroup) => {
    try { setApplyingKey(group.key); const next = await saveMarketUniverse({ preset: 'custom', customSymbolsText: (group.symbols || []).join('\n') }); message.success(`已应用到 Universe：${group.name} → ${next.symbolCount} 个标的`); window.dispatchEvent(new Event('qmt-market-universe-updated')); window.dispatchEvent(new Event('qmt-market-auto-refresh-updated')); window.dispatchEvent(new Event('qmt-downloaded-datasets-updated')); onChanged(); }
    catch (error) { message.error(error instanceof Error ? error.message : String(error)); }
    finally { setApplyingKey(''); }
  };
  const columns: ColumnsType<QmtUniverseGroup> = [
    { title: '列表', dataIndex: 'name', width: 190 },
    { title: '状态', dataIndex: 'status', width: 90, render: statusTag },
    { title: '标的数', dataIndex: 'symbolCount', width: 90 },
    { title: '同步时间', dataIndex: 'syncedAt', width: 170, render: formatMarketTime },
    { title: 'QMT sector 调用', dataIndex: 'sectorResults', render: (items?: QmtUniverseGroup['sectorResults']) => <Space wrap>{(items || []).map((x) => <Tag key={x.sector} color={x.status === 'READY' ? 'green' : x.status === 'EMPTY' ? 'gold' : 'red'}>{x.sector}:{x.count}</Tag>)}</Space> },
    { title: '操作', width: 150, render: (_, row) => <Button size="small" disabled={!row.symbolCount} loading={applyingKey === row.key} onClick={() => apply(row)}>应用到Universe</Button> },
  ];
  return <Space direction="vertical" style={{ width: '100%' }} size={12}>
    <Alert type="info" showIcon message="量化研究通常需要大盘行情。大盘/基准指数用于计算相对收益、Beta、市场状态、择时过滤、回撤对照和风控阈值，所以已加入同步列表。" />
    <Space wrap><Button type="primary" size="small" loading={running} onClick={run}>同步QMT真实列表</Button>{statusTag(sync.status)}<Tag color="cyan">总标的：{sync.totalSymbolCount || 0}</Tag><span className="muted">{sync.message}</span></Space>
    <Table rowKey="key" size="small" dataSource={sync.groups || []} columns={columns} pagination={false} scroll={{ x: 980 }} locale={{ emptyText: <EmptyState text="尚未同步 QMT 真实股票列表；点击上方按钮后会调用 xtdata.get_stock_list_in_sector。" /> }} />
  </Space>;
}

function UniverseControl({ onChanged }: { onChanged: () => void }) {
  const [state, setState] = useState<MarketUniverseStatus>(universeFallback);
  const load = async () => { try { setState(await getMarketUniverseStatus()); } catch { setState(universeFallback); } };
  useEffect(() => { load(); window.addEventListener('qmt-market-universe-updated', load); return () => window.removeEventListener('qmt-market-universe-updated', load); }, []);
  return <Space direction="vertical" style={{ width: '100%' }} size={12}>
    <Space wrap><Tag color="blue">当前Universe：{state.name}</Tag><Tag color="cyan">标的数：{state.symbolCount}</Tag><Tag color="purple">来源：{state.source === 'custom' ? 'QMT同步/自定义' : '系统默认'}</Tag><span className="muted">点击下方同步结果表的“应用到Universe”，自动刷新行情会按该列表下载本地缺失缓存。</span></Space>
    <QmtUniverseSyncControl onChanged={onChanged} />
  </Space>;
}

function DownloadedDataList() {
  const data = useAsync(getDownloadedDatasetStatus, downloadedFallback);
  const columns: ColumnsType<DownloadedDatasetRow> = [
    { title: '数据名称', dataIndex: 'name', width: 190 },
    { title: '类型', dataIndex: 'type', width: 130 },
    { title: '状态', dataIndex: 'status', width: 90, render: statusTag },
    { title: '记录数', dataIndex: 'recordCount', width: 90, render: (v) => Number(v || 0).toLocaleString() },
    { title: '数据时间区间', dataIndex: 'timeRange', width: 260, render: (v) => v || '-' },
    { title: '更新时间', dataIndex: 'updatedAt', width: 170, render: formatMarketTime },
    { title: '说明', dataIndex: 'note' },
    { title: '产物路径', dataIndex: 'sourcePath', width: 280, render: (v) => <Typography.Text copyable ellipsis style={{ maxWidth: 260 }}>{v}</Typography.Text> },
  ];
  return <Section title="当前已下载的数据列表" extra={<Tag color="green">已就绪 {data.readyCount}/{data.totalCount}</Tag>}>
    <Table rowKey="key" size="small" dataSource={data.rows || []} columns={columns} scroll={{ x: 1360, y: 320 }} locale={{ emptyText: <EmptyState text="暂无已下载数据；先同步 QMT 真实列表或开启自动刷新行情。" /> }} />
  </Section>;
}

export function MarketDataPage() {
  const sources = useAsync(getDataSources, [] as DataSourceStatus[]);
  const quotes = useAsync(getMarketQuotes, [] as MarketQuoteRow[]);
  const summary = useAsync(getMarketSummary, { quoteCount: 0, symbolCount: 0, upCount: 0, downCount: 0, flatCount: 0, latestTime: '', realMarketData: false, sandboxFallback: true, dataMode: 'UNKNOWN' } as MarketSummary);
  const [analysis, setAnalysis] = useState<MarketAIAnalysis | undefined>();
  const [analysisError, setAnalysisError] = useState<string>('');
  const [analyzing, setAnalyzing] = useState(false);
  const [refreshTick, setRefreshTick] = useState(0);
  const latestTime = useMemo(() => latestMarketTime(quotes, summary.latestTime), [quotes, summary.latestTime]);
  const analyze = async () => { try { setAnalyzing(true); setAnalysisError(''); const res = await runMarketAIAnalysis(); setAnalysis(res); message.success('AI 行情分析完成'); } catch (error) { const text = error instanceof Error ? error.message : String(error); setAnalysisError(text); message.error(text); } finally { setAnalyzing(false); } };
  useEffect(() => { if (refreshTick > 0) window.dispatchEvent(new Event('qmt-task-finished')); }, [refreshTick]);
  const columns: ColumnsType<MarketQuoteRow> = [{ title: '代码', dataIndex: 'symbol', fixed: 'left', width: 130 }, { title: '名称', dataIndex: 'name', width: 130 }, { title: '时间', dataIndex: 'time', width: 180, render: formatMarketTime }, { title: '最新价', dataIndex: 'latest', width: 100, render: price }, { title: '涨跌', dataIndex: 'change', width: 100, render: (v) => <span className={Number(v) >= 0 ? 'up' : 'down'}>{price(v)}</span> }, { title: '涨跌幅', dataIndex: 'changePct', width: 100, render: (v) => <span className={Number(v) >= 0 ? 'up' : 'down'}>{price(v)}%</span> }, { title: '开盘', dataIndex: 'open', width: 90, render: price }, { title: '最高', dataIndex: 'high', width: 90, render: price }, { title: '最低', dataIndex: 'low', width: 90, render: price }, { title: '收盘', dataIndex: 'close', width: 90, render: price }, { title: '成交量', dataIndex: 'volume', width: 120, render: (v) => Number(v || 0).toLocaleString() }, { title: '成交额', dataIndex: 'amount', width: 120, render: money }, { title: '状态', dataIndex: 'status', width: 100, render: statusTag }];
  return <div className="page-grid">
    <Section title="行情自动刷新控制" extra={<Tag color="green">只读 / dry-run / 不触发交易</Tag>}><AutoRefreshControl onChanged={() => setRefreshTick((x) => x + 1)} /></Section>
    <Section title={<Space size={10}><span>行情数据用途</span><Button size="small" type="primary" loading={analyzing} onClick={analyze}>AI 分析行情</Button></Space>}><Typography.Paragraph>行情数据是量化系统的“价格与成交事实层”，用于生成 K 线、计算收益率和波动率、更新因子、触发策略信号、估算成交成本、校验停牌/涨跌停/流动性，并为回测、仿真、影子实盘和风控提供统一输入。大盘/基准指数行情也需要同步，用来做相对收益、Beta、市场状态、择时过滤、回撤对照和风控判断。</Typography.Paragraph><Space wrap><Tag color="cyan">采集：QMT xtdata / 本地缓存 / 外部数据源</Tag><Tag color="green">清洗：复权 / 对齐 / 去异常 / 去重复</Tag><Tag color="gold">校验：延迟 / 缺失 / 异常 / 覆盖率</Tag><Tag color="purple">服务：因子研究 / 策略信号 / 风控 / 监控复盘</Tag></Space></Section>
    <Section title="行情 Universe / QMT真实列表同步" extra={<Tag color="blue">决定自动刷新下载哪些标的</Tag>}><UniverseControl onChanged={() => setRefreshTick((x) => x + 1)} /></Section>
    <DownloadedDataList />
    <Row gutter={[16, 16]}><Col xs={24} md={8}><Card className="metric-card"><b>行情记录数</b><div className="metric-value">{summary.quoteCount}</div><span>当前快照记录数量</span></Card></Col><Col xs={24} md={8}><Card className="metric-card"><b>Universe 标的数</b><div className="metric-value">{summary.universeSymbolCount || summary.symbolCount}</div><span>{summary.universeName || '当前行情池'}；缓存标的 {summary.symbolCount}</span></Card></Col><Col xs={24} md={8}><Card className="metric-card"><b>最新时间</b><div className="metric-value" style={{ fontSize: 18 }}>{latestTime}</div><Space wrap>{dataModeTag(summary)}<span>{summary.sandboxFallback ? '当前为沙盒样例时间，不是真实市场时间' : '用于判断行情是否滞后'}</span></Space></Card></Col></Row>
    <Section title="AI 行情分析报告"><AnalysisReport report={analysis} error={analysisError} /></Section>
    <Section title="数据源状态"><Typography.Paragraph type="secondary">用于查看行情来源是否健康，例如 QMT / xtdata、Tick、分钟线、日线等数据源是否可用、更新时间、延迟、缺失率和异常率。</Typography.Paragraph><Row gutter={[16, 16]}>{sources.map((s) => <Col xs={24} sm={12} lg={6} key={`${s.name}-${s.qualityLevel || ''}`}><Card className="source-card"><Space direction="vertical"><Space><b>{s.name}</b>{statusTag(String(s.status))}</Space><span>更新时间：{formatMarketTime(s.updatedAt || '-')}</span><span>今日记录：{Number(s.records || 0).toLocaleString()}</span><span>延迟：{s.latency}</span><span>质量：{s.qualityLevel || '-'}</span><span>缺失/异常：{s.missingRate}% / {s.abnormalRate}%</span></Space></Card></Col>)}</Row></Section>
    <Section title="行情明细表"><Typography.Paragraph type="secondary">用于查看已经获取并缓存到本地的具体行情记录，包括代码、时间、开高低收、成交量和成交额。表格默认每页显示 100 行，可切换 20 / 50 / 100 / 200 行。</Typography.Paragraph><Table rowKey={(record, index) => `${record.symbol}-${record.time}-${index ?? 0}`} size="small" dataSource={quotes} columns={columns} pagination={{ defaultPageSize: 100, pageSizeOptions: [20, 50, 100, 200], showSizeChanger: true }} scroll={{ x: 1380, y: 520 }} locale={{ emptyText: <EmptyState text="暂无行情明细；开启自动刷新行情后，系统会按 Universe 从本地 QMT / xtdata 获取并缓存。" /> }} /></Section>
  </div>;
}
