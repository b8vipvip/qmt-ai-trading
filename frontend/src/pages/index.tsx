import { Button, Card, Col, Descriptions, Divider, Form, Input, InputNumber, Modal, Row, Segmented, Space, Table, Tabs, Tag, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { BarChart, DrawdownChart, EquityCurveChart } from '../components/charts';
import { ConfirmDangerActionModal, EventLogPanel, MetricCard, RiskGauge, RiskLevelBadge, StatusBadge } from '../components/common';
import { BacktestReportPanel, OrderStatusTimeline, RiskRuleTable, StrategyStatusTable } from '../components/trading';
import { getBacktestReport, getBacktestTasks } from '../services/backtestService';
import { getDataQualityRows, getDataSources, getDataTasks } from '../services/dataService';
import { getDeploymentStages } from '../services/deploymentService';
import { getEquityCurve, getSystemEvents, getDashboardOverview, getStrategyStatusList } from '../services/dashboardService';
import { getOrderList, getTargetHoldings, getTradeList } from '../services/executionService';
import { getFactorDetail, getFactorList } from '../services/factorService';
import { getRealtimeMonitoring, getAttribution, getExecutionQuality, getDailyReview } from '../services/monitoringService';
import { getRiskEvents, getRiskOverview, getRiskRules } from '../services/riskService';
import { getApiStatus, getAuditLogs } from '../services/systemService';
import { getStrategyDetail, getStrategyList, getRebalancePlan } from '../services/strategyService';
import type { BacktestTask, DataQualityRow, DataSourceStatus, DataTaskRow, FactorRow, HoldingRow, OrderRow, RiskEvent, RiskRule, StrategyStatus, SystemEvent, TradeRow } from '../types';

function useAsync<T>(loader: () => Promise<T>, fallback: T): T {
  const [data, setData] = useState<T>(fallback);
  useEffect(() => { loader().then(setData).catch(() => setData(fallback)); }, []);
  return data;
}

function Section({ title, extra, children }: { title: string; extra?: React.ReactNode; children: React.ReactNode }) {
  return <Card className="section-card" title={title} extra={extra}>{children}</Card>;
}

export function DashboardPage() {
  const overview = useAsync(getDashboardOverview, { metrics: [], riskOverview: {} as any });
  const strategies = useAsync(getStrategyStatusList, [] as StrategyStatus[]);
  const curve = useAsync(getEquityCurve, []);
  const events = useAsync(getSystemEvents, [] as SystemEvent[]);
  const [danger, setDanger] = useState('');
  return <div className="page-grid"><Row gutter={[16, 16]}>{overview.metrics.map((m) => <Col xs={24} sm={12} lg={6} xl={6} key={m.title}><MetricCard item={m} /></Col>)}</Row><Row gutter={[16, 16]}><Col xs={24} xl={16}><Section title="账户资产曲线" extra={<Segmented options={['今日','近7日','近30日','近90日','今年','全部']} defaultValue="近90日" />}><EquityCurveChart data={curve} /></Section></Col><Col xs={24} xl={8}><Section title="实时风险面板"><Row gutter={[12, 12]}><Col span={12}><RiskGauge title="单票集中度" value={overview.riskOverview.concentration ?? 0} /></Col><Col span={12}><RiskGauge title="行业集中度" value={overview.riskOverview.industry ?? 0} /></Col><Col span={12}><RiskGauge title="总仓位" value={overview.riskOverview.total ?? 0} /></Col><Col span={12}><RiskGauge title="当日亏损" value={overview.riskOverview.dayLoss ?? 0} /></Col></Row></Section></Col></Row><Section title="策略运行状态"><StrategyStatusTable data={strategies} onDanger={setDanger} /></Section><Section title="系统事件流"><EventLogPanel events={events} /></Section><ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认停止交易" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} /></div>;
}

export function DataCenterPage() {
  const sources = useAsync(getDataSources, [] as DataSourceStatus[]);
  const quality = useAsync(getDataQualityRows, [] as DataQualityRow[]);
  const tasks = useAsync(getDataTasks, [] as DataTaskRow[]);
  return <div className="page-grid"><Row gutter={[16, 16]}>{sources.map((s) => <Col xs={24} sm={12} lg={6} key={s.name}><Card className="source-card"><Space direction="vertical"><Space><b>{s.name}</b><StatusBadge status={s.status} /></Space><span>更新时间：{s.updatedAt}</span><span>今日记录：{s.records.toLocaleString()}</span><span>延迟：{s.latency}</span><span>缺失/异常：{s.missingRate}% / {s.abnormalRate}%</span></Space></Card></Col>)}</Row><Section title="数据质量表"><Table rowKey="dataset" size="small" dataSource={quality} columns={[{ title:'数据集', dataIndex:'dataset' },{ title:'交易日', dataIndex:'tradeDate' },{ title:'覆盖股票数', dataIndex:'stockCount' },{ title:'缺失字段数', dataIndex:'missingFields' },{ title:'异常值数量', dataIndex:'abnormalValues' },{ title:'重复记录数', dataIndex:'duplicateRows' },{ title:'校验', dataIndex:'passed', render:(v)=> <Tag color={v?'green':'red'}>{v?'通过':'失败'}</Tag> },{ title:'操作', render:()=> <Space><Button size="small">查看详情</Button><Button size="small">重新清洗</Button></Space> }]} scroll={{ x: 900 }} /></Section><Section title="数据任务列表"><Table rowKey="name" size="small" dataSource={tasks} columns={[{ title:'任务名称', dataIndex:'name' },{ title:'任务类型', dataIndex:'type' },{ title:'执行周期', dataIndex:'cron' },{ title:'上次执行时间', dataIndex:'lastRun' },{ title:'下次执行时间', dataIndex:'nextRun' },{ title:'状态', dataIndex:'status', render:(v)=> <Tag color={v==='SUCCESS'?'green':'blue'}>{v}</Tag> },{ title:'耗时', dataIndex:'cost' },{ title:'操作', render:()=> <Button size="small">运行</Button> }]} scroll={{ x: 1000 }} /></Section></div>;
}

export function FactorsPage() {
  const factors = useAsync(getFactorList, [] as FactorRow[]);
  const detail = useAsync(() => getFactorDetail('factor-1'), null as any);
  return <div className="page-grid"><Section title="因子库"><Table rowKey="id" size="small" dataSource={factors} columns={[{ title:'因子名称', dataIndex:'name' },{ title:'类型', dataIndex:'type' },{ title:'版本', dataIndex:'version' },{ title:'股票池', dataIndex:'universe' },{ title:'IC均值', dataIndex:'icMean' },{ title:'Rank IC', dataIndex:'rankIc' },{ title:'ICIR', dataIndex:'icir' },{ title:'多空收益', dataIndex:'longShortReturn', render:(v)=> <span className="up">{v}%</span> },{ title:'换手率', dataIndex:'turnover' },{ title:'状态', dataIndex:'status', render:(v)=> <Tag color={v==='已上线'?'green':v==='已下线'?'default':'blue'}>{v}</Tag> },{ title:'操作', render:()=> <Space><Button size="small">查看分析</Button><Button size="small">加入组合</Button><Button size="small">下线</Button></Space> }]} scroll={{ x: 1200 }} /></Section>{detail && <Section title="因子详情：价值低估"><Tabs items={[{key:'base',label:'基本信息',children:<Descriptions column={2} bordered size="small" items={[{key:'1',label:'计算公式',children:'rank(EP) + rank(BP) - risk_neutralize(industry,size)'},{key:'2',label:'最近计算日志',children:'计算完成，覆盖 5100 只股票。'}]} />},{key:'ic',label:'IC 曲线',children:<EquityCurveChart data={detail.icSeries} />},{key:'layers',label:'分层收益',children:<BarChart names={['Q1','Q2','Q3','Q4','Q5']} values={detail.layers} title="分层收益" />},{key:'exposure',label:'暴露分析',children:<Row gutter={16}><Col span={12}><BarChart names={['金融','消费','科技','制造']} values={[12,18,9,15]} title="行业暴露" /></Col><Col span={12}><BarChart names={['小盘','中盘','大盘']} values={[8,22,31]} title="市值暴露" /></Col></Row>}]} /></Section>}</div>;
}

export function StrategiesPage() {
  const strategies = useAsync(getStrategyList, [] as StrategyStatus[]);
  const detail = useAsync(() => getStrategyDetail('s1'), null as any);
  const plan = useAsync(getRebalancePlan, null as any);
  const [danger, setDanger] = useState('');
  return <div className="page-grid"><Section title="策略列表"><StrategyStatusTable data={strategies} onDanger={setDanger} /></Section>{detail && <Section title="策略详情"><Tabs items={[{key:'base',label:'基本信息',children:<Descriptions column={3} bordered size="small" items={[{key:'1',label:'策略',children:detail.strategy.name},{key:'2',label:'股票池',children:detail.strategy.pool},{key:'3',label:'调仓周期',children:detail.strategy.rebalance}]} />},{key:'signal',label:'信号规则',children:'多因子排序 + 风险中性化 + 行业暴露约束。'},{key:'portfolio',label:'组合构建',children:<Table size="small" rowKey="code" dataSource={detail.holdings} columns={[{title:'股票',dataIndex:'name'},{title:'当前权重',dataIndex:'currentWeight'},{title:'目标权重',dataIndex:'targetWeight'}]} />},{key:'risk',label:'风控配置',children:'单票上限 10%，行业上限 25%，最大回撤 8%。'},{key:'backtest',label:'回测结果',children:<DrawdownChart data={[]} />},{key:'live',label:'实盘表现',children:'当前处于影子/仿真阶段。'},{key:'logs',label:'日志',children:<EventLogPanel events={[]} />}]} /></Section>}{plan && <Section title="调仓计划"><Table rowKey="code" size="small" dataSource={plan.holdings} columns={[{title:'股票代码',dataIndex:'code'},{title:'股票名称',dataIndex:'name'},{title:'当前持仓',dataIndex:'currentQty'},{title:'当前权重',dataIndex:'currentWeight'},{title:'目标权重',dataIndex:'targetWeight'},{title:'建议买卖数量',dataIndex:'diffQty'},{title:'差异金额',dataIndex:'diffAmount'},{title:'风控',dataIndex:'riskStatus',render:(v)=> <RiskLevelBadge level={v} />}]} scroll={{ x: 1000, y: 260 }} /><Typography.Text type="warning">{plan.notice}</Typography.Text></Section>}<ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认停止交易" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} /></div>;
}

export function BacktestPage() {
  const tasks = useAsync(getBacktestTasks, [] as BacktestTask[]);
  const report = useAsync(() => getBacktestReport('bt-1'), null as any);
  const [open, setOpen] = useState(false);
  return <div className="page-grid"><Section title="回测任务列表" extra={<Button type="primary" onClick={() => setOpen(true)}>创建回测任务</Button>}><Table rowKey="id" size="small" dataSource={tasks} columns={[{title:'任务名称',dataIndex:'name'},{title:'策略名称',dataIndex:'strategy'},{title:'股票池',dataIndex:'universe'},{title:'回测区间',dataIndex:'range'},{title:'初始资金',dataIndex:'capital'},{title:'调仓周期',dataIndex:'rebalance'},{title:'状态',dataIndex:'status',render:(v)=> <Tag color={v==='SUCCESS'?'green':'blue'}>{v}</Tag>},{title:'创建时间',dataIndex:'createdAt'},{title:'耗时',dataIndex:'cost'},{title:'操作',render:()=> <Space><Button size="small">查看报告</Button><Button size="small">复制任务</Button><Button size="small" danger>删除</Button></Space>}]} scroll={{ x: 1200 }} /></Section>{report && <Section title="回测报告"><BacktestReportPanel task={report.task} /><Row gutter={16}><Col span={16}><EquityCurveChart data={report.curve} /></Col><Col span={8}><Descriptions column={1} bordered size="small" items={Object.entries(report.metrics).map(([k,v]) => ({ key:k, label:k, children:String(v) }))} /></Col></Row></Section>}<Modal open={open} onCancel={() => setOpen(false)} onOk={() => setOpen(false)} title="创建回测任务"><Form layout="vertical"><Form.Item label="策略"><Input defaultValue="沪深300 ETF 动量轮动" /></Form.Item><Form.Item label="股票池"><Input defaultValue="沪深300" /></Form.Item><Row gutter={12}><Col span={12}><Form.Item label="开始日期"><Input defaultValue="2021-01-01" /></Form.Item></Col><Col span={12}><Form.Item label="结束日期"><Input defaultValue="2026-07-05" /></Form.Item></Col></Row><Form.Item label="初始资金"><InputNumber style={{width:'100%'}} defaultValue={1000000} /></Form.Item><Form.Item label="滑点模型"><Input defaultValue="固定滑点 + 冲击成本" /></Form.Item></Form></Modal></div>;
}

export function DeploymentPage() {
  const stages = useAsync(getDeploymentStages, [] as any[]);
  const [danger, setDanger] = useState('');
  return <div className="page-grid deployment-board">{stages.map((s) => <Card key={s.stage} className={`stage-card ${s.stage.includes('Full') ? 'critical' : ''}`} title={s.stage} extra={<Tag color={s.status.includes('LOCKED')?'red':'blue'}>{s.status}</Tag>}><Descriptions column={1} size="small" items={[{key:'1',label:'开始时间',children:s.startedAt},{key:'2',label:'运行天数',children:s.days},{key:'3',label:'策略数量',children:s.strategyCount},{key:'4',label:'资金规模',children:s.capital},{key:'5',label:'当前问题',children:s.issues}]} /><Divider /><b>通过标准</b><ul>{s.criteria.map((c:string) => <li key={c}>{c}</li>)}</ul><Button danger={s.stage.includes('Full')} onClick={() => setDanger(`阶段推进：${s.stage}`)}>{s.stage.includes('Full') ? '申请进入正式实盘' : '提交阶段复核'}</Button></Card>)}<ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认风险已知" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} /></div>;
}

export function ExecutionPage() {
  const holdings = useAsync(getTargetHoldings, [] as HoldingRow[]);
  const orders = useAsync(getOrderList, [] as OrderRow[]);
  const trades = useAsync(getTradeList, [] as TradeRow[]);
  const [danger, setDanger] = useState('');
  return <div className="page-grid"><Section title="目标持仓"><Table rowKey="code" size="small" dataSource={holdings} columns={[{title:'股票代码',dataIndex:'code'},{title:'股票名称',dataIndex:'name'},{title:'当前持仓',dataIndex:'currentQty'},{title:'当前权重',dataIndex:'currentWeight'},{title:'目标权重',dataIndex:'targetWeight'},{title:'目标市值',dataIndex:'targetValue'},{title:'需要买入/卖出数量',dataIndex:'diffQty'},{title:'差异金额',dataIndex:'diffAmount'},{title:'风控状态',dataIndex:'riskStatus',render:(v)=> <RiskLevelBadge level={v} />}]} scroll={{ x: 1200, y: 280 }} /></Section><Section title="订单计划"><Table rowKey="id" size="small" dataSource={orders} columns={[{title:'订单编号',dataIndex:'id'},{title:'策略名称',dataIndex:'strategy'},{title:'股票代码',dataIndex:'code'},{title:'方向',dataIndex:'side',render:(v)=> <Tag color={v==='买入'?'red':'green'}>{v}</Tag>},{title:'计划数量',dataIndex:'quantity'},{title:'计划价格',dataIndex:'price'},{title:'预计金额',dataIndex:'amount'},{title:'风控检查',dataIndex:'riskCheck',render:(v)=> v==='PASS'?<Tag color="green">PASS</Tag>:<RiskLevelBadge level={v} />},{title:'状态',dataIndex:'status'},{title:'操作',fixed:'right',render:(_,row)=> <Space><Button size="small" danger onClick={() => setDanger(`提交订单：${row.id}`)}>提交</Button><Button size="small" onClick={() => setDanger(`取消订单：${row.id}`)}>取消</Button></Space>}]} scroll={{ x: 1400, y: 300 }} /></Section><Row gutter={16}><Col span={12}><Section title="订单状态流转"><OrderStatusTimeline status={orders[3]?.status ?? 'CREATED'} /></Section></Col><Col span={12}><Section title="成交记录"><Table rowKey="id" size="small" dataSource={trades} columns={[{title:'成交编号',dataIndex:'id'},{title:'订单编号',dataIndex:'orderId'},{title:'股票',dataIndex:'name'},{title:'方向',dataIndex:'side'},{title:'成交数量',dataIndex:'quantity'},{title:'成交价格',dataIndex:'price'},{title:'成交金额',dataIndex:'amount'},{title:'成交时间',dataIndex:'time'}]} scroll={{ x: 900, y: 260 }} pagination={false} /></Section></Col></Row><ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认执行交易动作" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} /></div>;
}

export function RiskCenterPage() {
  const overview = useAsync(getRiskOverview, {} as any);
  const rules = useAsync(getRiskRules, [] as RiskRule[]);
  const events = useAsync(getRiskEvents, [] as RiskEvent[]);
  const [danger, setDanger] = useState('');
  return <div className="page-grid"><Row gutter={[16,16]}>{['level','triggerCount','blockedOrders','totalPosition','maxSinglePosition','maxIndustryExposure','intradayLoss','currentDrawdown','losingDays'].map((k) => <Col xs={12} md={8} xl={4} key={k}><Card className="risk-kpi"><span>{k}</span><b>{String(overview[k] ?? '-')}</b></Card></Col>)}</Row><Section title="风控规则表" extra={<Space><Button danger onClick={() => setDanger('暂停全部策略')}>暂停全部策略</Button><Button danger onClick={() => setDanger('停止自动交易')}>停止自动交易</Button><Button danger onClick={() => setDanger('一键撤单')}>一键撤单</Button><Button danger onClick={() => setDanger('一键平仓')}>一键平仓</Button></Space>}><RiskRuleTable data={rules} onDanger={setDanger} /></Section><Section title="风控事件记录"><Table rowKey="id" size="small" dataSource={events} columns={[{title:'时间',dataIndex:'time'},{title:'策略',dataIndex:'strategy'},{title:'规则名称',dataIndex:'rule'},{title:'风险等级',dataIndex:'level',render:(v)=> <RiskLevelBadge level={v} />},{title:'触发值',dataIndex:'trigger'},{title:'阈值',dataIndex:'threshold'},{title:'处理动作',dataIndex:'action'},{title:'处理结果',dataIndex:'result'},{title:'操作人',dataIndex:'operator'}]} scroll={{ x: 1100, y: 330 }} /></Section><ConfirmDangerActionModal open={!!danger} title={danger} confirmText="确认停止交易" onCancel={() => setDanger('')} onConfirm={() => setDanger('')} /></div>;
}

export function MonitoringPage() {
  const realtime = useAsync(getRealtimeMonitoring, null as any);
  const attribution = useAsync(getAttribution, [] as any[]);
  const quality = useAsync(getExecutionQuality, {} as any);
  const review = useAsync(getDailyReview, null as any);
  return <div className="page-grid">{realtime && <Section title="实时监控"><Row gutter={16}><Col span={16}><EquityCurveChart data={realtime.curve} /></Col><Col span={8}><Descriptions column={1} bordered size="small" items={Object.entries(realtime.latency).map(([k,v])=>({key:k,label:k,children:String(v)}))} /></Col></Row></Section>}<Row gutter={16}><Col span={12}><Section title="收益归因"><BarChart names={attribution.map(i=>i.name)} values={attribution.map(i=>i.value)} /></Section></Col><Col span={12}><Section title="成交质量"><Descriptions column={2} bordered size="small" items={Object.entries(quality).map(([k,v])=>({key:k,label:k,children:String(v)}))} /></Section></Col></Row>{review && <Section title="每日复盘"><Typography.Paragraph>{review.summary}</Typography.Paragraph><EventLogPanel events={review.events} /></Section>}</div>;
}

export function SettingsPage() {
  const apiStatus = useAsync(getApiStatus, [] as any[]);
  const logs = useAsync(getAuditLogs, [] as any[]);
  return <div className="page-grid"><Section title="配置中心"><Descriptions bordered column={3} size="small" items={[{key:'mode',label:'交易模式',children:'研究 / 仿真'},{key:'pool',label:'默认股票池',children:'沪深300'},{key:'fee',label:'默认手续费',children:'万2.5'},{key:'slippage',label:'默认滑点',children:'3bp'},{key:'risk',label:'默认风控规则',children:'启用'},{key:'backtest',label:'默认回测参数',children:'T+1 / 涨跌停 / 停牌检测'}]} /></Section><Section title="API 接口状态"><Table rowKey="name" size="small" dataSource={apiStatus} columns={[{title:'接口',dataIndex:'name'},{title:'状态',dataIndex:'status',render:(v)=> <StatusBadge status={v} />},{title:'延迟',dataIndex:'latency'}]} pagination={false} /></Section><Section title="日志审计"><Table rowKey={(r:any)=>`${r.time}-${r.action}`} size="small" dataSource={logs} columns={[{title:'时间',dataIndex:'time'},{title:'用户',dataIndex:'user'},{title:'模块',dataIndex:'module'},{title:'操作',dataIndex:'action'},{title:'IP',dataIndex:'ip'},{title:'结果',dataIndex:'result'}]} scroll={{ y: 300 }} /></Section></div>;
}
