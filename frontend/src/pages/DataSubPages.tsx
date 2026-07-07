import { Button, Card, Col, Descriptions, Row, Space, Table, Tag, Typography, message } from 'antd';
import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { EmptyState, SourcePathTag } from '../components/common';
import { TaskRunButton } from '../components/common/TaskRunButton';
import { getDataQualityRows, getDataTasks } from '../services/dataService';
import { getFundamentalRecords, getFundamentalSources, getNewsItems, getQualityOverview, getTaskCatalog } from '../services/dataPagesService';
import type { FundamentalRecordRow, FundamentalSourceRow, NewsItemRow, QualityOverview, TaskCatalogRow } from '../services/dataPagesService';
import { getApiConfigs, testApiConfig } from '../services/systemManagementService';
import type { ApiConfigRow } from '../services/systemManagementService';
import type { DataQualityRow, DataTaskRow } from '../types';

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

function metric(title: string, value: ReactNode, extra?: ReactNode) {
  return <Card className="metric-card"><b>{title}</b><div className="metric-value">{value}</div>{extra}</Card>;
}

function configRows(configs: ApiConfigRow[], purpose: string) {
  return configs.filter((x) => x.enabled && ((x.purposes || []).includes(purpose) || (x.purposes || []).includes('all')));
}

function ApiTestButton({ id }: { id: string }) {
  const [loading, setLoading] = useState(false);
  const run = async () => {
    try {
      setLoading(true);
      const res = await testApiConfig(id);
      if (res.status === 'READY') message.success(res.message);
      else message.warning(res.message);
    } catch (error) {
      message.error(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  };
  return <Button size="small" loading={loading} onClick={run}>测试连接</Button>;
}

function apiConfigTable(configs: ApiConfigRow[]) {
  return <Table rowKey="id" size="small" dataSource={configs} columns={[{title:'名称',dataIndex:'name'},{title:'Provider',dataIndex:'provider',render:(v)=><Tag color="blue">{v}</Tag>},{title:'用途',dataIndex:'purposes',render:(v:string[])=>(v || []).map((x)=><Tag key={x}>{x}</Tag>)},{title:'Base URL',dataIndex:'baseUrl'},{title:'Token',dataIndex:'tokenMasked',render:(v,r)=><Tag color={r.hasToken?'green':'default'}>{r.hasToken ? v : '未配置'}</Tag>},{title:'启用',dataIndex:'enabled',render:(v)=><Tag color={v?'green':'default'}>{String(v)}</Tag>},{title:'来源',dataIndex:'sourcePath',render:(v)=><SourcePathTag value={v}/>},{title:'操作',render:(_,row)=><ApiTestButton id={row.id}/>}]} scroll={{ x: 1100 }} pagination={false} locale={{ emptyText: <EmptyState text="暂无已分配用途的真实数据 API；请到 系统管理 → API 接口 新增接口，再到 配置中心 分配用途。" /> }} />;
}

export function FundamentalDataPage() {
  const sources = useAsync(getFundamentalSources, [] as FundamentalSourceRow[]);
  const records = useAsync(getFundamentalRecords, [] as FundamentalRecordRow[]);
  const configs = useAsync(getApiConfigs, [] as ApiConfigRow[]);
  const related = configRows(configs, 'fundamental');
  return <div className="page-grid">
    <Section title="基本面真实 API 配置" extra={<Tag color="green">不再伪造 PE/PB/ROE</Tag>}>{apiConfigTable(related)}</Section>
    <Row gutter={[16, 16]}>{sources.map((s) => <Col xs={24} md={8} key={s.name}><Card className="source-card"><Space direction="vertical"><Space><b>{s.name}</b><Tag color={s.status === 'READY' ? 'green' : 'gold'}>{s.status}</Tag></Space><span>Provider：{(s as any).provider || '-'}</span><span>记录数：{s.records}</span><span>覆盖：{s.coverage}</span><span>延迟：{s.latency}</span><span>缺失率：{s.missingRate}%</span><SourcePathTag value={s.sourcePath} /></Space></Card></Col>)}</Row>
    <Section title="基本面记录"><Table rowKey="symbol" size="small" dataSource={records} columns={[{title:'代码',dataIndex:'symbol'},{title:'名称',dataIndex:'name'},{title:'报告期',dataIndex:'reportDate'},{title:'PE',dataIndex:'pe'},{title:'PB',dataIndex:'pb'},{title:'ROE',dataIndex:'roe'},{title:'营收增长',dataIndex:'revenueGrowth'},{title:'净利增长',dataIndex:'netProfitGrowth'},{title:'状态',dataIndex:'status',render:(v)=><Tag color={v==='READY'?'green':'gold'}>{v}</Tag>},{title:'来源',dataIndex:'sourcePath',render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1200, y: 420 }} locale={{ emptyText: <EmptyState text="暂无真实基本面产物。先在 API 接口新增 Tushare/AkShare/BaoStock，再到配置中心分配“基本面”用途。" /> }} /></Section>
    <Section title="接口说明"><Descriptions bordered size="small" column={2} items={[{key:'1',label:'API 配置来源',children:'/api/v1/frontend/system/api-configs'},{key:'2',label:'记录接口',children:'/api/v1/frontend/data/fundamental-records'},{key:'3',label:'产物文件',children:'artifacts/reports/console/datahub/fundamental_latest.json'},{key:'4',label:'当前原则',children:'没有真实产物就显示空状态，不展示模拟财务数值'}]} /></Section>
  </div>;
}

export function NewsDataPage() {
  const items = useAsync(getNewsItems, [] as NewsItemRow[]);
  const configs = useAsync(getApiConfigs, [] as ApiConfigRow[]);
  const related = configRows(configs, 'news');
  return <div className="page-grid">
    <Section title="公告新闻真实 API 配置" extra={<Tag color="green">不再用任务日志冒充新闻</Tag>}>{apiConfigTable(related)}</Section>
    <Row gutter={[16, 16]}><Col xs={24} md={8}>{metric('真实新闻记录', items.length)}</Col><Col xs={24} md={8}>{metric('已配置新闻源', related.length)}</Col><Col xs={24} md={8}>{metric('高影响事件', items.filter((x)=>x.impact==='HIGH').length)}</Col></Row>
    <Section title="公告新闻事件流"><Table rowKey="id" size="small" dataSource={items} columns={[{title:'时间',dataIndex:'time',width:180},{title:'类型',dataIndex:'type',width:120},{title:'标题/内容',dataIndex:'title'},{title:'关联标的',dataIndex:'symbols',width:120},{title:'情绪',dataIndex:'sentiment',width:100,render:(v)=><Tag>{v}</Tag>},{title:'影响',dataIndex:'impact',width:100,render:(v)=><Tag color={v==='HIGH'?'red':v==='MEDIUM'?'gold':'green'}>{v}</Tag>},{title:'来源',dataIndex:'source',width:120},{title:'产物',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1200, y: 520 }} locale={{ emptyText: <EmptyState text="暂无真实公告新闻产物。先新增公告/新闻 API，再到配置中心分配“公告新闻”用途。" /> }} /></Section>
    <Section title="接口说明"><Descriptions bordered size="small" column={2} items={[{key:'1',label:'新闻事件接口',children:'/api/v1/frontend/data/news-items'},{key:'2',label:'产物文件',children:'artifacts/reports/console/datahub/news_latest.json'},{key:'3',label:'配置入口',children:'系统管理 → API 接口 / 配置中心 → API 用途配置'},{key:'4',label:'安全边界',children:'只用于研究和监控，不直接下单'}]} /></Section>
  </div>;
}

export function DataQualityPage() {
  const overview = useAsync(getQualityOverview, { datasetCount:0, passedCount:0, failedCount:0, warningCount:0, recordCount:0, symbolCount:0 } as QualityOverview);
  const quality = useAsync(getDataQualityRows, [] as DataQualityRow[]);
  return <div className="page-grid">
    <Section title="数据质量任务"><Space wrap><TaskRunButton taskId="data_cache_check" type="primary">缓存质量检查</TaskRunButton><TaskRunButton taskId="qmt_data_diagnostics_readonly">QMT 只读诊断</TaskRunButton><TaskRunButton taskId="xtdata_live_readonly_smoke">刷新行情产物</TaskRunButton><TaskRunButton taskId="market_snapshot_readonly">行情快照</TaskRunButton></Space></Section>
    <Row gutter={[16,16]}><Col xs={12} md={4}>{metric('数据集', overview.datasetCount)}</Col><Col xs={12} md={4}>{metric('通过', overview.passedCount)}</Col><Col xs={12} md={4}>{metric('失败', overview.failedCount)}</Col><Col xs={12} md={4}>{metric('警告', overview.warningCount)}</Col><Col xs={12} md={4}>{metric('记录数', overview.recordCount)}</Col><Col xs={12} md={4}>{metric('标的数', overview.symbolCount)}</Col></Row>
    <Section title="质量检查明细" extra={<SourcePathTag value={overview.sourcePath} />}><Table rowKey="dataset" size="small" dataSource={quality} columns={[{ title:'数据集', dataIndex:'dataset' },{ title:'交易日', dataIndex:'tradeDate' },{ title:'覆盖股票数', dataIndex:'stockCount' },{ title:'缺失字段数', dataIndex:'missingFields' },{ title:'异常值数量', dataIndex:'abnormalValues' },{ title:'重复记录数', dataIndex:'duplicateRows' },{ title:'校验', dataIndex:'passed', render:(v)=> <Tag color={v?'green':'red'}>{v?'通过':'失败'}</Tag> },{ title:'来源', dataIndex:'sourcePath', render:(v)=> <SourcePathTag value={v} /> },{ title:'操作', render:()=> <Space><TaskRunButton taskId="qmt_data_diagnostics_readonly">诊断</TaskRunButton><TaskRunButton taskId="data_cache_check">检查缓存</TaskRunButton></Space> }]} scroll={{ x: 1200, y: 460 }} locale={{ emptyText: <EmptyState text="暂无质量产物；运行数据质量任务后自动生成。" /> }} /></Section>
  </div>;
}

export function DataTasksPage() {
  const history = useAsync(getDataTasks, [] as DataTaskRow[]);
  const catalog = useAsync(getTaskCatalog, [] as TaskCatalogRow[]);
  const dataTasks = catalog.filter((t) => ['DATA', 'RESEARCH', 'STRATEGY'].includes(t.category));
  return <div className="page-grid">
    <Section title="数据任务快捷启动"><Space wrap><TaskRunButton taskId="xtdata_live_readonly_smoke" type="primary">xtdata 只读 smoke</TaskRunButton><TaskRunButton taskId="market_snapshot_readonly">行情快照</TaskRunButton><TaskRunButton taskId="stage88_real_data_dry_run">真实数据链路</TaskRunButton><TaskRunButton taskId="factor_scan">因子扫描</TaskRunButton></Space></Section>
    <Section title="任务目录"><Table rowKey="task_id" size="small" dataSource={dataTasks} columns={[{title:'任务ID',dataIndex:'task_id'},{title:'名称',dataIndex:'title_zh'},{title:'分类',dataIndex:'category',render:(v)=><Tag color="blue">{v}</Tag>},{title:'说明',dataIndex:'description_zh'},{title:'安全模式',dataIndex:'safe_mode',render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'Dry-run',dataIndex:'dry_run_only',render:(v)=><Tag color={v?'green':'gold'}>{String(v)}</Tag>},{title:'产物',dataIndex:'output_artifacts',render:(v:string[])=> (v || []).join(', ')},{title:'操作',render:(_,row)=><TaskRunButton taskId={row.task_id}>运行</TaskRunButton>}]} scroll={{ x: 1400, y: 360 }} locale={{ emptyText: <EmptyState text="暂无任务目录；请检查 /api/v1/frontend/data/task-catalog。" /> }} /></Section>
    <Section title="任务历史"><Table rowKey={(r:any)=>`${r.name}-${r.lastRun}`} size="small" dataSource={history} columns={[{ title:'任务名称', dataIndex:'name' },{ title:'任务类型', dataIndex:'type' },{ title:'执行周期', dataIndex:'cron' },{ title:'上次执行时间', dataIndex:'lastRun' },{ title:'下次执行时间', dataIndex:'nextRun' },{ title:'状态', dataIndex:'status', render:(v)=> <Tag color={v==='SUCCESS'?'green':v==='FAILED'?'red':'blue'}>{v}</Tag> },{ title:'耗时', dataIndex:'cost' },{ title:'来源', dataIndex:'sourcePath', render:(v)=> <SourcePathTag value={v} /> }]} scroll={{ x: 1100, y: 360 }} locale={{ emptyText: <EmptyState text="暂无任务历史；点击上方任务运行后写入持久化 task_history。" /> }} /></Section>
  </div>;
}
