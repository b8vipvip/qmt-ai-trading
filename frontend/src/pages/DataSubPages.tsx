import { Alert, Button, Card, Col, message, Row, Space, Table, Tag, Typography } from 'antd';
import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { EmptyState, SourcePathTag } from '../components/common';
import { TaskRunButton } from '../components/common/TaskRunButton';
import { getDataCleaningIssues, getDataCleaningRuns, getDataCleaningStatus, getDataQualityRows, getDataTasks, runDataCleaning } from '../services/dataService';
import type { DataCleaningIssue, DataCleaningRun, DataCleaningStatus } from '../services/dataService';
import { getFundamentalRecords, getFundamentalSources, getNewsItems, getQualityOverview, getTaskCatalog } from '../services/dataPagesService';
import type { FundamentalRecordRow, FundamentalSourceRow, NewsItemRow, QualityOverview, TaskCatalogRow } from '../services/dataPagesService';
import type { DataQualityRow, DataTaskRow } from '../types';

function useAsync<T>(loader: () => Promise<T>, fallback: T): T {
  const [data, setData] = useState<T>(fallback);
  useEffect(() => {
    let mounted = true;
    const load = () => loader().then((v) => { if (mounted) setData(v); }).catch(() => { if (mounted) setData(fallback); });
    load();
    window.addEventListener('qmt-task-finished', load);
    window.addEventListener('qmt-api-config-saved', load);
    window.addEventListener('qmt-data-cleaning-finished', load);
    return () => { mounted = false; window.removeEventListener('qmt-task-finished', load); window.removeEventListener('qmt-api-config-saved', load); window.removeEventListener('qmt-data-cleaning-finished', load); };
  }, []);
  return data;
}

function Section({ title, extra, children }: { title: string; extra?: ReactNode; children: ReactNode }) {
  return <Card className="section-card" title={title} extra={extra}>{children}</Card>;
}

function metric(title: string, value: ReactNode, extra?: ReactNode) {
  return <Card className="metric-card"><b>{title}</b><div className="metric-value">{value}</div>{extra}</Card>;
}

function statusTag(value: string) {
  const text = String(value || 'UNKNOWN');
  return <Tag color={text === 'PASS' || text === 'READY' || text === 'SUCCESS' ? 'green' : text === 'WARN' || text === 'NO_DATA' ? 'gold' : text === 'FAIL' || text === 'FAILED' || text === 'ERROR' ? 'red' : 'default'}>{text}</Tag>;
}

function CleaningRunButton({ mode = 'full_pipeline', children, type = 'primary' }: { mode?: string; children: ReactNode; type?: 'primary' | 'default' | 'dashed' }) {
  const [loading, setLoading] = useState(false);
  async function run() {
    try {
      setLoading(true);
      const result = await runDataCleaning(mode);
      message.success(`数据清洗完成：${result.overview?.status || 'DONE'}，记录 ${Number(result.overview?.recordCount || 0).toLocaleString()} 条`);
      window.dispatchEvent(new Event('qmt-data-cleaning-finished'));
      window.dispatchEvent(new Event('qmt-task-finished'));
    } catch (error) {
      message.error(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }
  return <Button size="small" type={type} loading={loading} onClick={run}>{children}</Button>;
}

export function FundamentalDataPage() {
  const sources = useAsync(getFundamentalSources, [] as FundamentalSourceRow[]);
  const records = useAsync(getFundamentalRecords, [] as FundamentalRecordRow[]);
  return <div className="page-grid">
    <Row gutter={[16, 16]}>
      <Col xs={24} md={8}>{metric('基本面数据源', sources.length)}</Col>
      <Col xs={24} md={8}>{metric('基本面记录', records.length)}</Col>
      <Col xs={24} md={8}>{metric('可用记录', records.filter((x) => x.status === 'READY').length)}</Col>
    </Row>
    <Section title="基本面数据任务" extra={<Tag color="green">只读 / 不触发交易</Tag>}>
      <Space wrap>
        <TaskRunButton taskId="data_cache_check" type="primary">缓存质量检查</TaskRunButton>
        <TaskRunButton taskId="qmt_data_diagnostics_readonly">数据源诊断</TaskRunButton>
      </Space>
    </Section>
    <Section title="基本面数据源状态"><Row gutter={[16, 16]}>{sources.map((s) => <Col xs={24} md={8} key={s.name}><Card className="source-card"><Space direction="vertical"><Space><b>{s.name}</b><Tag color={s.status === 'READY' ? 'green' : 'gold'}>{s.status}</Tag></Space><span>Provider：{(s as any).provider || '-'}</span><span>记录数：{s.records}</span><span>覆盖：{s.coverage}</span><span>延迟：{s.latency}</span><span>缺失率：{s.missingRate}%</span><SourcePathTag value={s.sourcePath} /></Space></Card></Col>)}</Row></Section>
    <Section title="基本面记录"><Table rowKey="symbol" size="small" dataSource={records} columns={[{title:'代码',dataIndex:'symbol'},{title:'名称',dataIndex:'name'},{title:'报告期',dataIndex:'reportDate'},{title:'PE',dataIndex:'pe'},{title:'PB',dataIndex:'pb'},{title:'ROE',dataIndex:'roe'},{title:'营收增长',dataIndex:'revenueGrowth'},{title:'净利增长',dataIndex:'netProfitGrowth'},{title:'状态',dataIndex:'status',render:(v)=><Tag color={v==='READY'?'green':'gold'}>{v}</Tag>},{title:'来源',dataIndex:'sourcePath',render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1200, y: 420 }} locale={{ emptyText: <EmptyState text="暂无真实基本面产物。请先配置数据源并运行基本面采集任务。" /> }} /></Section>
  </div>;
}

export function NewsDataPage() {
  const items = useAsync(getNewsItems, [] as NewsItemRow[]);
  return <div className="page-grid">
    <Row gutter={[16, 16]}>
      <Col xs={24} md={8}>{metric('公告新闻记录', items.length)}</Col>
      <Col xs={24} md={8}>{metric('高影响事件', items.filter((x)=>x.impact==='HIGH').length)}</Col>
      <Col xs={24} md={8}>{metric('负面情绪', items.filter((x)=>x.sentiment==='NEGATIVE').length)}</Col>
    </Row>
    <Section title="公告新闻任务" extra={<Tag color="green">研究 / 监控用途，不触发交易</Tag>}>
      <Space wrap>
        <TaskRunButton taskId="data_cache_check" type="primary">缓存质量检查</TaskRunButton>
        <TaskRunButton taskId="qmt_data_diagnostics_readonly">数据源诊断</TaskRunButton>
      </Space>
    </Section>
    <Section title="公告新闻事件流"><Table rowKey="id" size="small" dataSource={items} columns={[{title:'时间',dataIndex:'time',width:180},{title:'类型',dataIndex:'type',width:120},{title:'标题/内容',dataIndex:'title'},{title:'关联标的',dataIndex:'symbols',width:120},{title:'情绪',dataIndex:'sentiment',width:100,render:(v)=><Tag>{v}</Tag>},{title:'影响',dataIndex:'impact',width:100,render:(v)=><Tag color={v==='HIGH'?'red':v==='MEDIUM'?'gold':'green'}>{v}</Tag>},{title:'来源',dataIndex:'source',width:120},{title:'产物',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1200, y: 520 }} locale={{ emptyText: <EmptyState text="暂无真实公告新闻产物。请先配置公告/新闻数据源并运行采集任务。" /> }} /></Section>
  </div>;
}

const cleaningFallback: DataCleaningStatus = { overview: { status: 'NO_DATA', datasetCount: 0, passedCount: 0, failedCount: 0, warningCount: 0, recordCount: 0, symbolCount: 0, issueCount: 0 }, rows: [], issues: [], runs: [], updatedAt: '' };

export function DataQualityPage() {
  const overview = useAsync(getQualityOverview, { datasetCount:0, passedCount:0, failedCount:0, warningCount:0, recordCount:0, symbolCount:0 } as QualityOverview);
  const cleaning = useAsync(getDataCleaningStatus, cleaningFallback);
  const quality = useAsync(getDataQualityRows, [] as DataQualityRow[]);
  const issues = useAsync(getDataCleaningIssues, [] as DataCleaningIssue[]);
  const o = cleaning.overview || overview;
  return <div className="page-grid">
    <Section title="数据质量任务" extra={<SourcePathTag value={o.sourcePath} />}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Alert type="info" showIcon message="数据质量页负责展示清洗结果、覆盖率、异常明细和问题标的；真正执行入口在数据任务页，这里也保留快捷执行。" />
        <Space wrap><CleaningRunButton>运行清洗流水线</CleaningRunButton><CleaningRunButton mode="quality_scan" type="default">仅扫描质量</CleaningRunButton><TaskRunButton taskId="qmt_data_diagnostics_readonly">QMT 只读诊断</TaskRunButton></Space>
      </Space>
    </Section>
    <Row gutter={[16,16]}><Col xs={12} md={4}>{metric('数据集', o.datasetCount)}</Col><Col xs={12} md={4}>{metric('通过', o.passedCount)}</Col><Col xs={12} md={4}>{metric('失败', o.failedCount)}</Col><Col xs={12} md={4}>{metric('警告', o.warningCount)}</Col><Col xs={12} md={4}>{metric('清洗记录', Number(o.recordCount || 0).toLocaleString())}</Col><Col xs={12} md={4}>{metric('问题数', Number((o as any).issueCount || 0).toLocaleString(), statusTag((o as any).status || 'NO_DATA'))}</Col></Row>
    <Section title="清洗质量明细"><Table rowKey={(r)=>`${r.dataset}-${r.period || ''}-${r.layer || ''}`} size="small" dataSource={quality} columns={[{ title:'数据集', dataIndex:'dataset', width:220 },{ title:'周期', dataIndex:'period', width:90 },{ title:'层级', dataIndex:'layer', width:150 },{ title:'时间区间', dataIndex:'timeRange', width:260, render:(v)=>v || '-' },{ title:'标的数', dataIndex:'stockCount', width:90 },{ title:'输入/清洗', render:(_,r)=>`${Number(r.inputRows || 0).toLocaleString()} / ${Number(r.recordCount || 0).toLocaleString()}`, width:130 },{ title:'缺失字段', dataIndex:'missingFields', width:100 },{ title:'异常值', dataIndex:'abnormalValues', width:90 },{ title:'重复', dataIndex:'duplicateRows', width:80 },{ title:'丢弃', dataIndex:'droppedRows', width:80 },{ title:'状态', dataIndex:'status', width:90, render:statusTag },{ title:'清洗产物', dataIndex:'cleanedPath', width:120, render:(v)=><SourcePathTag value={v}/> },{ title:'来源', dataIndex:'sourcePath', width:120, render:(v)=><SourcePathTag value={v}/> }]} scroll={{ x: 1700, y: 420 }} locale={{ emptyText: <EmptyState text="暂无质量产物；先在数据任务页运行数据清洗流水线。" /> }} /></Section>
    <Section title="问题明细"><Table rowKey="id" size="small" dataSource={issues} columns={[{ title:'级别', dataIndex:'level', width:90, render:statusTag },{ title:'类型', dataIndex:'type', width:140 },{ title:'数据集', dataIndex:'dataset', width:220 },{ title:'代码', dataIndex:'symbol', width:120 },{ title:'时间', dataIndex:'time', width:170 },{ title:'问题说明', dataIndex:'message' },{ title:'来源', dataIndex:'sourcePath', width:120, render:(v)=><SourcePathTag value={v}/> }]} scroll={{ x: 1300, y: 360 }} locale={{ emptyText: <EmptyState text="暂无问题明细；质量通过或尚未运行清洗。" /> }} /></Section>
  </div>;
}

export function DataTasksPage() {
  const history = useAsync(getDataTasks, [] as DataTaskRow[]);
  const cleaningRuns = useAsync(getDataCleaningRuns, [] as DataCleaningRun[]);
  const catalog = useAsync(getTaskCatalog, [] as TaskCatalogRow[]);
  const dataTasks = catalog.filter((t) => ['DATA', 'RESEARCH', 'STRATEGY'].includes(t.category));
  return <div className="page-grid">
    <Section title="数据清洗流水线" extra={<Tag color="green">真实后端逻辑 / 只读 / 不触发交易</Tag>}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Typography.Paragraph type="secondary" style={{ margin: 0 }}>执行字段标准化、代码/时间统一、OHLCV 校验、去重、异常值扫描，并把清洗后的数据写入 artifacts/reports/console/data_cleaning/cleaned，同时生成数据质量报告。</Typography.Paragraph>
        <Space wrap><CleaningRunButton>全量清洗流水线</CleaningRunButton><CleaningRunButton mode="quality_scan" type="default">质量扫描</CleaningRunButton><TaskRunButton taskId="qmt_data_diagnostics_readonly">QMT 只读诊断</TaskRunButton></Space>
      </Space>
    </Section>
    <Section title="清洗运行记录"><Table rowKey="runId" size="small" dataSource={cleaningRuns} columns={[{title:'运行ID',dataIndex:'runId',width:150},{title:'名称',dataIndex:'name',width:160},{title:'模式',dataIndex:'mode',width:120},{title:'状态',dataIndex:'status',width:90,render:statusTag},{title:'开始',dataIndex:'startedAt',width:170},{title:'完成',dataIndex:'finishedAt',width:170},{title:'数据集',dataIndex:'datasetCount',width:80},{title:'记录数',dataIndex:'recordCount',width:110,render:(v)=>Number(v||0).toLocaleString()},{title:'问题数',dataIndex:'issueCount',width:90},{title:'清洗文件',dataIndex:'cleanedFileCount',width:90},{title:'报告',dataIndex:'sourcePath',render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1300, y: 280 }} locale={{ emptyText: <EmptyState text="暂无清洗运行记录；点击上方全量清洗流水线后生成。" /> }} /></Section>
    <Section title="数据任务快捷启动"><Space wrap><TaskRunButton taskId="xtdata_live_readonly_smoke" type="primary">xtdata 只读 smoke</TaskRunButton><TaskRunButton taskId="market_snapshot_readonly">行情快照</TaskRunButton><TaskRunButton taskId="stage88_real_data_dry_run">真实数据链路</TaskRunButton><TaskRunButton taskId="factor_scan">因子扫描</TaskRunButton></Space></Section>
    <Section title="任务目录"><Table rowKey="task_id" size="small" dataSource={dataTasks} columns={[{title:'任务ID',dataIndex:'task_id'},{title:'名称',dataIndex:'title_zh'},{title:'分类',dataIndex:'category',render:(v)=><Tag color="blue">{v}</Tag>},{title:'说明',dataIndex:'description_zh'},{title:'安全模式',dataIndex:'safe_mode',render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'Dry-run',dataIndex:'dry_run_only',render:(v)=><Tag color={v?'green':'gold'}>{String(v)}</Tag>},{title:'产物',dataIndex:'output_artifacts',render:(v:string[])=> (v || []).join(', ')},{title:'操作',render:(_,row)=><TaskRunButton taskId={row.task_id}>运行</TaskRunButton>}]} scroll={{ x: 1400, y: 360 }} locale={{ emptyText: <EmptyState text="暂无任务目录；请检查 /api/v1/frontend/data/task-catalog。" /> }} /></Section>
    <Section title="任务历史"><Table rowKey={(r:any)=>`${r.name}-${r.lastRun}`} size="small" dataSource={history} columns={[{ title:'任务名称', dataIndex:'name' },{ title:'任务类型', dataIndex:'type' },{ title:'执行周期', dataIndex:'cron' },{ title:'上次执行时间', dataIndex:'lastRun' },{ title:'下次执行时间', dataIndex:'nextRun' },{ title:'状态', dataIndex:'status', render:(v)=> <Tag color={v==='SUCCESS'?'green':v==='FAILED'?'red':'blue'}>{v}</Tag> },{ title:'耗时', dataIndex:'cost' },{ title:'来源', dataIndex:'sourcePath', render:(v)=> <SourcePathTag value={v} /> }]} scroll={{ x: 1100, y: 360 }} locale={{ emptyText: <EmptyState text="暂无任务历史；点击上方任务运行后写入持久化 task_history。" /> }} /></Section>
  </div>;
}
