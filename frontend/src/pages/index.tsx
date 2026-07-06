import { Button, Card, Col, Descriptions, Divider, Form, Input, InputNumber, Modal, Row, Segmented, Space, Table, Tabs, Tag, Typography } from 'antd';
import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { BarChart, DrawdownChart, EquityCurveChart } from '../components/charts';
import { ConfirmDangerActionModal, EmptyState, EventLogPanel, MetricCard, RiskGauge, RiskLevelBadge, SourcePathTag, StatusBadge } from '../components/common';
import { BacktestReportPanel, OrderStatusTimeline, RiskRuleTable, StrategyStatusTable } from '../components/trading';
import { getBacktestReport, getBacktestTasks } from '../services/backtestService';
import { getDataQualityRows, getDataSources, getDataTasks } from '../services/dataService';
import { getDeploymentStages } from '../services/deploymentService';
import { getDashboardOverview, getEquityCurve, getStrategyStatusList, getSystemEvents } from '../services/dashboardService';
import { getOrderList, getTargetHoldings, getTradeList } from '../services/executionService';
import { getFactorDetail, getFactorList } from '../services/factorService';
import { getAttribution, getDailyReview, getExecutionQuality, getRealtimeMonitoring } from '../services/monitoringService';
import { getRiskEvents, getRiskOverview, getRiskRules } from '../services/riskService';
import { getApiStatus, getAuditLogs } from '../services/systemService';
import { getRebalancePlan, getStrategyDetail, getStrategyList } from '../services/strategyService';
import type { BacktestTask, DataQualityRow, DataSourceStatus, DataTaskRow, FactorRow, HoldingRow, OrderRow, RiskEvent, RiskRule, StrategyStatus, SystemEvent, TradeRow } from '../types';

function useAsync<T>(loader: () => Promise<T>, fallback: T): T {
  const [data, setData] = useState<T>(fallback);
  useEffect(() => { loader().then(setData).catch(() => setData(fallback)); }, []);
  return data;
}

function Section({ title, extra, children }: { title: string; extra?: ReactNode; children: ReactNode }) {
  return <Card className="section-card" title={title} extra={extra}>{children}</Card>;
}

function money(value: number | string | undefined) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? `¥${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : String(value ?? '-');
}

function percent(value: number | string | undefined) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? `${n}%` : String(value ?? '-');
}

const riskKpiLabels: Record<string, string> = {
  level: '当前风控等级',
  triggerCount: '今日触发次数',
  blockedOrders: '已拦截订单',
  totalPosition: '当前总仓位',
  maxSinglePosition: '单票最大仓位',
  maxIndustryExposure: '行业最大暴露',
  intradayLoss: '当日亏损',
  currentDrawdown: '当前回撤',
  losingDays: '连续亏损天数',
};

export function DashboardPage() {
  const overview = useAsync(getDashboardOverview, { metrics: [], riskOverview: {} as any });
  const strategies = useAsync(getStrategyStatusList, [] as StrategyStatus[]);
  const curve = useAsync(getEquityCurve, []);
  const events = useAsync(getSystemEvents, [] as SystemEvent[]);
  const [danger, setDanger] = useState('');
  const risk = overview.riskOverview || {};

  return <div className="page-grid">
    <Row gutter={[16, 16]}>{overview.metrics.map((m) => <Col xs={24} sm={12} lg={6} xl={6} key={m.title}><MetricCard item={m} /></Col>)}</Row>
    <Row gutter={[16, 16]}>
      <Col xs={24} xl={16}><Section title="账户资产曲线" extra={<Segmented options={['今日','近7日','近30日','近90日','今年','全部']} defaultValue="近90日" />}><EquityCurveChart data={curve} /></Section></Col>
      <Col xs={24} xl={8}><Section title="实时风险面板" extra={<SourcePathTag value={risk.sourcePath} />}><Row gutter={[12, 12]}><Col span={12}><RiskGauge title="单票集中度" value={risk.concentration ?? 0} /></Col><Col span={12}><RiskGauge title="行业集中度" value={risk.industry ?? 0} /></Col><Col span={12}><RiskGauge title="总仓位" value={risk.total ?? risk.totalPosition ?? 0} /></Col><Col span={12}><RiskGauge title="当日亏损" value={risk.dayLoss ?? 0} /></Col></Row></Section></Col>
    </Row>
    <Section title="策略运行状态"><StrategyStatusTable data={strategies} onDanger={setDanger} /></Section>
    <Section title="系统事件流"><EventLogPanel events={events} /></Section>
    <ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认停止交易" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} />
  </div>;
}

export function DataCenterPage() {
  const sources = useAsync(getDataSources, [] as DataSourceStatus[]);
  const quality = useAsync(getDataQualityRows, [] as DataQualityRow[]);
  const tasks = useAsync(getDataTasks, [] as DataTaskRow[]);
  return <div className="page-grid">
    <Row gutter={[16, 16]}>{sources.map((s) => <Col xs={24} sm={12} lg={6} key={s.name}><Card className="source-card"><Space direction="vertical"><Space><b>{s.name}</b><StatusBadge status={s.status} /></Space><span>更新时间：{s.updatedAt || '-'}</span><span>今日记录：{Number(s.records || 0).toLocaleString()}</span><span>延迟：{s.latency}</span><span>质量：{s.qualityLevel || '-'}</span><span>缺失/异常：{s.missingRate}% / {s.abnormalRate}%</span><SourcePathTag value={s.sourcePath} /></Space></Card></Col>)}</Row>
    <Section title="数据质量表"><Table rowKey="dataset" size="small" dataSource={quality} columns={[{ title:'数据集', dataIndex:'dataset' },{ title:'交易日', dataIndex:'tradeDate' },{ title:'覆盖股票数', dataIndex:'stockCount' },{ title:'缺失字段数', dataIndex:'missingFields' },{ title:'异常值数量', dataIndex:'abnormalValues' },{ title:'重复记录数', dataIndex:'duplicateRows' },{ title:'校验', dataIndex:'passed', render:(v)=> <Tag color={v?'green':'red'}>{v?'通过':'失败'}</Tag> },{ title:'来源', dataIndex:'sourcePath', render:(v)=> <SourcePathTag value={v} /> },{ title:'操作', render:()=> <Space><Button size="small">查看详情</Button><Button size="small">重新清洗</Button></Space> }]} scroll={{ x: 1100 }} locale={{ emptyText: <EmptyState text="暂无数据质量产物；运行行情读取或数据质量任务后生成。" /> }} /></Section>
    <Section title="数据任务列表"><Table rowKey={(r:any)=>`${r.name}-${r.lastRun}`} size="small" dataSource={tasks} columns={[{ title:'任务名称', dataIndex:'name' },{ title:'任务类型', dataIndex:'type' },{ title:'执行周期', dataIndex:'cron' },{ title:'上次执行时间', dataIndex:'lastRun' },{ title:'下次执行时间', dataIndex:'nextRun' },{ title:'状态', dataIndex:'status', render:(v)=> <Tag color={v==='SUCCESS'?'green':v==='FAILED'?'red':'blue'}>{v}</Tag> },{ title:'耗时', dataIndex:'cost' },{ title:'来源', dataIndex:'sourcePath', render:(v)=> <SourcePathTag value={v} /> },{ title:'操作', render:()=> <Button size="small">运行</Button> }]} scroll={{ x: 1200 }} locale={{ emptyText: <EmptyState text="暂无任务历史；在工作台运行任务后会写入 task_history。" /> }} /></Section>
  </div>;
}

export function FactorsPage() {
  const factors = useAsync(getFactorList, [] as FactorRow[]);
  const detail = useAsync(() => getFactorDetail(factors[0]?.id || 'factor-1'), null as any);
  const activeFactor = factors[0] || detail?.factor;
  return <div className="page-grid">
    <Section title="因子库 / 后端候选池"><Table rowKey="id" size="small" dataSource={factors} columns={[{ title:'因子名称', dataIndex:'name' },{ title:'类型', dataIndex:'type' },{ title:'版本', dataIndex:'version' },{ title:'股票池/标的', dataIndex:'universe' },{ title:'评分', dataIndex:'score' },{ title:'排名', dataIndex:'rank' },{ title:'IC均值', dataIndex:'icMean' },{ title:'Rank IC', dataIndex:'rankIc' },{ title:'ICIR', dataIndex:'icir' },{ title:'原因', dataIndex:'reasons' },{ title:'风险提示', dataIndex:'riskFlags' },{ title:'状态', dataIndex:'status', render:(v)=> <Tag color={v==='已上线'?'green':v==='已下线'?'default':'blue'}>{v}</Tag> },{ title:'来源', dataIndex:'sourcePath', render:(v)=> <SourcePathTag value={v} /> },{ title:'操作', render:()=> <Space><Button size="small">查看分析</Button><Button size="small">加入组合</Button><Button size="small">下线</Button></Space> }]} scroll={{ x: 1700 }} locale={{ emptyText: <EmptyState text="暂无因子候选；请运行 factor_scan。" /> }} /></Section>
    {activeFactor && <Section title={`因子详情：${activeFactor.name}`}><Tabs items={[{key:'base',label:'基本信息',children:<Descriptions column={2} bordered size="small" items={[{key:'1',label:'标的/股票池',children:activeFactor.universe},{key:'2',label:'后端评分',children:String(activeFactor.score ?? '-')},{key:'3',label:'原因',children:activeFactor.reasons || '等待 research reasons 产物'},{key:'4',label:'来源',children:<SourcePathTag value={activeFactor.sourcePath} />}]} />},{key:'ic',label:'IC 曲线',children:<EquityCurveChart data={detail?.icSeries || []} />},{key:'layers',label:'分层收益',children:<BarChart names={['Q1','Q2','Q3','Q4','Q5']} values={detail?.layers || []} title="分层收益" />},{key:'exposure',label:'暴露分析',children:<Row gutter={16}><Col span={12}><BarChart names={['金融','消费','科技','制造']} values={[12,18,9,15]} title="行业暴露" /></Col><Col span={12}><BarChart names={['小盘','中盘','大盘']} values={[8,22,31]} title="市值暴露" /></Col></Row>}]} /></Section>}
  </div>;
}

export function StrategiesPage() {
  const strategies = useAsync(getStrategyList, [] as StrategyStatus[]);
  const detail = useAsync(() => getStrategyDetail(strategies[0]?.id || 's1'), null as any);
  const plan = useAsync(getRebalancePlan, null as any);
  const [danger, setDanger] = useState('');
  return <div className="page-grid">
    <Section title="策略列表 / Strategy artifacts"><StrategyStatusTable data={strategies} onDanger={setDanger} /></Section>
    {detail && <Section title="策略详情"><Tabs items={[{key:'base',label:'基本信息',children:<Descriptions column={3} bordered size="small" items={[{key:'1',label:'策略',children:detail.strategy.name},{key:'2',label:'股票池',children:detail.strategy.pool},{key:'3',label:'调仓周期',children:detail.strategy.rebalance},{key:'4',label:'最新信号',children:detail.strategy.lastAction || '-'},{key:'5',label:'来源',children:<SourcePathTag value={detail.strategy.sourcePath} />}]} />},{key:'signal',label:'信号规则',children:'当前接入 strategy_signals / trade_intents 后端产物；后续再接策略编辑器。'},{key:'portfolio',label:'组合构建',children:<Table size="small" rowKey="code" dataSource={detail.holdings} columns={[{title:'股票',dataIndex:'name'},{title:'当前权重',dataIndex:'currentWeight'},{title:'目标权重',dataIndex:'targetWeight'},{title:'来源',dataIndex:'sourcePath',render:(v)=> <SourcePathTag value={v} />}]} locale={{ emptyText: <EmptyState /> }} />},{key:'risk',label:'风控配置',children:'单票上限、行业上限、最大回撤等由 Risk Gate 后端闸门执行。'},{key:'backtest',label:'回测结果',children:<DrawdownChart data={[]} />},{key:'live',label:'实盘表现',children:'当前处于 dry-run / shadow / read-only 阶段，不允许真实发单。'},{key:'logs',label:'日志',children:<EventLogPanel events={[]} />}]} /></Section>}
    {plan && <Section title="调仓计划 / 只进风控不下单"><Table rowKey="code" size="small" dataSource={plan.holdings} columns={[{title:'股票代码',dataIndex:'code'},{title:'股票名称',dataIndex:'name'},{title:'当前持仓',dataIndex:'currentQty'},{title:'当前权重',dataIndex:'currentWeight'},{title:'目标权重',dataIndex:'targetWeight'},{title:'建议买卖数量',dataIndex:'diffQty'},{title:'差异金额',dataIndex:'diffAmount',render:money},{title:'风控',dataIndex:'riskStatus',render:(v)=> <RiskLevelBadge level={v} />},{title:'来源',dataIndex:'sourcePath',render:(v)=> <SourcePathTag value={v} />}]} scroll={{ x: 1200, y: 260 }} locale={{ emptyText: <EmptyState /> }} /><Typography.Text type="warning">{plan.notice}</Typography.Text></Section>}
    <ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认停止交易" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} />
  </div>;
}

export function BacktestPage() {
  const tasks = useAsync(getBacktestTasks, [] as BacktestTask[]);
  const report = useAsync(() => getBacktestReport(tasks[0]?.id || 'bt-1'), null as any);
  const [open, setOpen] = useState(false);
  return <div className="page-grid">
    <Section title="回测任务列表" extra={<Button type="primary" onClick={() => setOpen(true)}>创建回测任务</Button>}><Table rowKey="id" size="small" dataSource={tasks} columns={[{title:'任务名称',dataIndex:'name'},{title:'策略名称',dataIndex:'strategy'},{title:'股票池',dataIndex:'universe'},{title:'回测区间',dataIndex:'range'},{title:'初始资金',dataIndex:'capital',render:money},{title:'调仓周期',dataIndex:'rebalance'},{title:'状态',dataIndex:'status',render:(v)=> <Tag color={v==='SUCCESS'?'green':v==='DATA_MISSING'?'default':'blue'}>{v}</Tag>},{title:'创建时间',dataIndex:'createdAt'},{title:'耗时',dataIndex:'cost'},{title:'来源',dataIndex:'sourcePath',render:(v)=> <SourcePathTag value={v} />},{title:'操作',render:()=> <Space><Button size="small">查看报告</Button><Button size="small">复制任务</Button><Button size="small" danger>删除</Button></Space>}]} scroll={{ x: 1400 }} locale={{ emptyText: <EmptyState text="暂无回测报告；请运行 shadow replay 或回测任务。" /> }} /></Section>
    {report && <Section title="回测报告"><BacktestReportPanel task={report.task} /><Row gutter={16}><Col span={16}><EquityCurveChart data={report.curve} /></Col><Col span={8}><Descriptions column={1} bordered size="small" items={Object.entries(report.metrics).map(([k,v]) => ({ key:k, label:k, children:String(v) }))} /></Col></Row></Section>}
    <Modal open={open} onCancel={() => setOpen(false)} onOk={() => setOpen(false)} title="创建回测任务"><Form layout="vertical"><Form.Item label="策略"><Input defaultValue="沪深300 ETF 动量轮动" /></Form.Item><Form.Item label="股票池"><Input defaultValue="沪深300" /></Form.Item><Row gutter={12}><Col span={12}><Form.Item label="开始日期"><Input defaultValue="2021-01-01" /></Form.Item></Col><Col span={12}><Form.Item label="结束日期"><Input defaultValue="2026-07-05" /></Form.Item></Col></Row><Form.Item label="初始资金"><InputNumber style={{width:'100%'}} defaultValue={1000000} /></Form.Item><Form.Item label="滑点模型"><Input defaultValue="固定滑点 + 冲击成本" /></Form.Item></Form></Modal>
  </div>;
}

export function DeploymentPage() {
  const stages = useAsync(getDeploymentStages, [] as any[]);
  const [danger, setDanger] = useState('');
  return <div className="page-grid deployment-board">{stages.map((s) => <Card key={s.stage} className={`stage-card ${s.stage.includes('Full') ? 'critical' : ''}`} title={s.stage} extra={<Tag color={String(s.status).includes('LOCKED')?'red':'blue'}>{s.status}</Tag>}><Descriptions column={1} size="small" items={[{key:'1',label:'开始时间',children:s.startedAt},{key:'2',label:'运行天数',children:s.days},{key:'3',label:'策略数量',children:s.strategyCount},{key:'4',label:'资金规模',children:s.capital},{key:'5',label:'当前问题',children:s.issues},{key:'6',label:'来源',children:<SourcePathTag value={s.sourcePath} />}]} /><Divider /><b>通过标准</b><ul>{(s.criteria || []).map((c:string) => <li key={c}>{c}</li>)}</ul><Button danger={s.stage.includes('Full')} onClick={() => setDanger(`阶段推进：${s.stage}`)}>{s.stage.includes('Full') ? '申请进入正式实盘' : '提交阶段复核'}</Button></Card>)}<ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认风险已知" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} /></div>;
}

export function ExecutionPage() {
  const holdings = useAsync(getTargetHoldings, [] as HoldingRow[]);
  const orders = useAsync(getOrderList, [] as OrderRow[]);
  const trades = useAsync(getTradeList, [] as TradeRow[]);
  const [danger, setDanger] = useState('');
  return <div className="page-grid">
    <Section title="目标持仓 / Account readonly + Portfolio preview"><Table rowKey="code" size="small" dataSource={holdings} columns={[{title:'股票代码',dataIndex:'code'},{title:'股票名称',dataIndex:'name'},{title:'当前持仓',dataIndex:'currentQty'},{title:'当前权重',dataIndex:'currentWeight',render:percent},{title:'目标权重',dataIndex:'targetWeight'},{title:'目标市值',dataIndex:'targetValue',render:money},{title:'需要买入/卖出数量',dataIndex:'diffQty'},{title:'差异金额',dataIndex:'diffAmount',render:money},{title:'风控状态',dataIndex:'riskStatus',render:(v)=> <RiskLevelBadge level={v} />},{title:'来源',dataIndex:'sourcePath',render:(v)=> <SourcePathTag value={v} />}]} scroll={{ x: 1400, y: 280 }} locale={{ emptyText: <EmptyState text="暂无持仓或订单预览产物；请运行 account_readonly_dry_run / order_preview_dry_run。" /> }} /></Section>
    <Section title="订单计划 / Preview only"><Table rowKey="id" size="small" dataSource={orders} columns={[{title:'预览编号',dataIndex:'id'},{title:'意图/策略',dataIndex:'strategy'},{title:'股票代码',dataIndex:'code'},{title:'方向',dataIndex:'side',render:(v)=> <Tag color={v==='买入'?'red':'green'}>{v}</Tag>},{title:'原始方向',dataIndex:'rawSide'},{title:'计划数量',dataIndex:'quantity'},{title:'最新价',dataIndex:'latestPrice'},{title:'计划价格',dataIndex:'price'},{title:'预计金额',dataIndex:'estimatedAmount',render:money},{title:'风控决策',dataIndex:'riskDecision'},{title:'风控检查',dataIndex:'riskCheck',render:(v)=> v==='PASS'?<Tag color="green">PASS</Tag>:<RiskLevelBadge level={v} />},{title:'业务状态',dataIndex:'businessStatus'},{title:'仅预览',dataIndex:'previewOnly',render:(v)=> <Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'可提交',dataIndex:'canSubmit',render:(v)=> <Tag color={v?'red':'green'}>{String(v)}</Tag>},{title:'来源',dataIndex:'sourcePath',render:(v)=> <SourcePathTag value={v} />},{title:'操作',render:(_,row)=> <Space><Button size="small" danger disabled={!row.canSubmit} onClick={() => setDanger(`提交订单：${row.id}`)}>提交</Button><Button size="small" onClick={() => setDanger(`取消订单：${row.id}`)}>取消</Button></Space>}]} scroll={{ x: 2000, y: 320 }} locale={{ emptyText: <EmptyState text="暂无订单预览；请运行 order_preview_dry_run。" /> }} /></Section>
    <Row gutter={16}><Col span={12}><Section title="订单状态流转"><OrderStatusTimeline status={orders[0]?.status ?? 'CREATED'} /></Section></Col><Col span={12}><Section title="成交记录"><Table rowKey="id" size="small" dataSource={trades} columns={[{title:'成交编号',dataIndex:'id'},{title:'订单编号',dataIndex:'orderId'},{title:'股票',dataIndex:'name'},{title:'方向',dataIndex:'side'},{title:'成交数量',dataIndex:'quantity'},{title:'成交价格',dataIndex:'price'},{title:'成交金额',dataIndex:'amount',render:money},{title:'成交时间',dataIndex:'time'},{title:'来源',dataIndex:'sourcePath',render:(v)=> <SourcePathTag value={v} />}]} scroll={{ x: 1000, y: 260 }} pagination={false} locale={{ emptyText: <EmptyState text="真实成交记录未接入；当前阶段不展示 mock 成交。" /> }} /></Section></Col></Row>
    <ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认执行交易动作" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} />
  </div>;
}

export function RiskCenterPage() {
  const overview = useAsync(getRiskOverview, {} as any);
  const rules = useAsync(getRiskRules, [] as RiskRule[]);
  const events = useAsync(getRiskEvents, [] as RiskEvent[]);
  const [danger, setDanger] = useState('');
  return <div className="page-grid">
    <Row gutter={[16,16]}>{Object.keys(riskKpiLabels).map((k) => <Col xs={12} md={8} xl={4} key={k}><Card className="risk-kpi"><span>{riskKpiLabels[k]}</span><b>{k === 'level' ? String(overview[k] ?? '-') : String(overview[k] ?? 0)}</b></Card></Col>)}</Row>
    <Section title="风控规则表" extra={<Space><Button danger onClick={() => setDanger('暂停全部策略')}>暂停全部策略</Button><Button danger onClick={() => setDanger('停止自动交易')}>停止自动交易</Button><Button danger onClick={() => setDanger('一键撤单')}>一键撤单</Button><Button danger onClick={() => setDanger('一键平仓')}>一键平仓</Button></Space>}><RiskRuleTable data={rules} onDanger={setDanger} /></Section>
    <Section title="风控事件记录"><Table rowKey="id" size="small" dataSource={events} columns={[{title:'时间',dataIndex:'time'},{title:'策略',dataIndex:'strategy'},{title:'规则名称',dataIndex:'rule'},{title:'风险等级',dataIndex:'level',render:(v)=> <RiskLevelBadge level={v} />},{title:'触发值',dataIndex:'trigger'},{title:'阈值',dataIndex:'threshold'},{title:'处理动作',dataIndex:'action'},{title:'处理结果',dataIndex:'result'},{title:'操作人',dataIndex:'operator'},{title:'来源',dataIndex:'sourcePath',render:(v)=> <SourcePathTag value={v} />}]} scroll={{ x: 1300, y: 330 }} locale={{ emptyText: <EmptyState text="暂无风控事件；运行 risk_gate_dry_run 后显示。" /> }} /></Section>
    <ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认停止交易" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} />
  </div>;
}

export function MonitoringPage() {
  const realtime = useAsync(getRealtimeMonitoring, null as any);
  const attribution = useAsync(getAttribution, [] as any[]);
  const quality = useAsync(getExecutionQuality, {} as any);
  const review = useAsync(getDailyReview, null as any);
  return <div className="page-grid">
    {realtime && <Section title="实时监控"><Row gutter={16}><Col span={16}><EquityCurveChart data={realtime.curve} /></Col><Col span={8}><Descriptions column={1} bordered size="small" items={Object.entries(realtime.latency || {}).map(([k,v])=>({key:k,label:k,children:String(v)}))} /></Col></Row></Section>}
    <Row gutter={16}><Col span={12}><Section title="收益归因"><BarChart names={attribution.map(i=>i.name)} values={attribution.map(i=>i.value)} /></Section></Col><Col span={12}><Section title="成交质量"><Descriptions column={2} bordered size="small" items={Object.entries(quality).map(([k,v])=>({key:k,label:k,children:String(v)}))} /></Section></Col></Row>
    {review && <Section title="每日复盘"><Typography.Paragraph>{review.summary}</Typography.Paragraph><EventLogPanel events={review.events} /></Section>}
  </div>;
}

export function SettingsPage() {
  const apiStatus = useAsync(getApiStatus, [] as any[]);
  const logs = useAsync(getAuditLogs, [] as any[]);
  return <div className="page-grid">
    <Section title="配置中心"><Descriptions bordered column={3} size="small" items={[{key:'mode',label:'交易模式',children:'研究 / 仿真'},{key:'pool',label:'默认股票池',children:'沪深300'},{key:'fee',label:'默认手续费',children:'万2.5'},{key:'slippage',label:'默认滑点',children:'3bp'},{key:'risk',label:'默认风控规则',children:'启用'},{key:'backtest',label:'默认回测参数',children:'T+1 / 涨跌停 / 停牌检测'}]} /></Section>
    <Section title="API 接口状态"><Table rowKey="name" size="small" dataSource={apiStatus} columns={[{title:'接口',dataIndex:'name'},{title:'状态',dataIndex:'status',render:(v)=> <StatusBadge status={v} />},{title:'延迟',dataIndex:'latency'},{title:'来源',dataIndex:'sourcePath',render:(v)=> <SourcePathTag value={v} />}]} pagination={false} locale={{ emptyText: <EmptyState /> }} /></Section>
    <Section title="日志审计"><Table rowKey={(r:any)=>`${r.time}-${r.action}`} size="small" dataSource={logs} columns={[{title:'时间',dataIndex:'time'},{title:'用户',dataIndex:'user'},{title:'模块',dataIndex:'module'},{title:'操作',dataIndex:'action'},{title:'IP',dataIndex:'ip'},{title:'结果',dataIndex:'result'}]} scroll={{ y: 300 }} locale={{ emptyText: <EmptyState text="暂无审计日志；系统事件生成后自动映射。" /> }} /></Section>
  </div>;
}
