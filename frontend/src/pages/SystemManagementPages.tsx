import { Card, Col, Descriptions, Row, Space, Table, Tag, Typography } from 'antd';
import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { EmptyState, SourcePathTag } from '../components/common';
import { TaskRunButton } from '../components/common/TaskRunButton';
import { getSystemApiRows, getSystemAuditRows, getSystemConfigRows, getSystemPermissionRows, getSystemSummary } from '../services/systemManagementService';
import type { ApiRow, AuditRow, ConfigRow, PermissionRow, SystemSummary } from '../services/systemManagementService';

function useAsync<T>(loader: () => Promise<T>, fallback: T): T {
  const [data, setData] = useState<T>(fallback);
  useEffect(() => {
    let mounted = true;
    const load = () => loader().then((v) => { if (mounted) setData(v); }).catch(() => { if (mounted) setData(fallback); });
    load();
    window.addEventListener('qmt-task-finished', load);
    return () => { mounted = false; window.removeEventListener('qmt-task-finished', load); };
  }, []);
  return data;
}

function Section({ title, extra, children }: { title: string; extra?: ReactNode; children: ReactNode }) {
  return <Card className="section-card" title={title} extra={extra}>{children}</Card>;
}

function statusTag(value: string) {
  const text = String(value || 'UNKNOWN');
  const color = ['READY', 'SUCCESS', 'NORMAL'].includes(text) ? 'green' : ['ERROR', 'FAILED'].includes(text) ? 'red' : 'gold';
  return <Tag color={color}>{text}</Tag>;
}

function metric(title: string, value: ReactNode) {
  return <Card className="metric-card"><b>{title}</b><div className="metric-value">{value}</div></Card>;
}

export function SystemConfigPage() {
  const summary = useAsync(getSystemSummary, { artifactRoot: '', taskCount: 0, historyCount: 0, latestRunAt: '', liveTradingEnabled: false, orderSubmitEnabled: false, orderCancelEnabled: false } as SystemSummary);
  const rows = useAsync(getSystemConfigRows, [] as ConfigRow[]);
  return <div className="page-grid">
    <Section title="系统配置任务"><Space wrap><TaskRunButton taskId="workflow_dry_run_check" type="primary">系统链路检查</TaskRunButton><TaskRunButton taskId="list_latest_reports">刷新报告列表</TaskRunButton><TaskRunButton taskId="ai_model_discovery">AI 模型发现</TaskRunButton></Space></Section>
    <Row gutter={[16,16]}><Col xs={12} md={6}>{metric('白名单任务', summary.taskCount)}</Col><Col xs={12} md={6}>{metric('历史运行', summary.historyCount)}</Col><Col xs={12} md={6}>{metric('发单开关', String(summary.orderSubmitEnabled))}</Col><Col xs={12} md={6}>{metric('实盘开关', String(summary.liveTradingEnabled))}</Col></Row>
    <Section title="配置中心 / 只读真实配置"><Table rowKey="key" size="small" dataSource={rows} columns={[{title:'配置键',dataIndex:'key',width:180},{title:'配置项',dataIndex:'name',width:180},{title:'当前值',dataIndex:'value',render:(v,r)=><Typography.Text code={r.sensitive}> {String(v || '-')} </Typography.Text>},{title:'可编辑',dataIndex:'editable',width:90,render:(v)=><Tag color={v?'gold':'green'}>{String(v)}</Tag>},{title:'敏感',dataIndex:'sensitive',width:80,render:(v)=><Tag color={v?'red':'green'}>{String(v)}</Tag>},{title:'来源',dataIndex:'source',width:240}]} scroll={{ x: 1100, y: 480 }} locale={{ emptyText: <EmptyState text="未读取到系统配置。" /> }} /></Section>
    <Section title="安全说明"><Descriptions bordered size="small" column={2} items={[{key:'1',label:'产物目录',children:summary.artifactRoot},{key:'2',label:'最新任务时间',children:summary.latestRunAt || '-'},{key:'3',label:'密钥展示策略',children:'不显示 .env/token/secret/key 明文'},{key:'4',label:'交易安全',children:'orderSubmit/liveTrading 固定为 false'}]} /></Section>
  </div>;
}

export function SystemApiPage() {
  const rows = useAsync(getSystemApiRows, [] as ApiRow[]);
  return <div className="page-grid">
    <Section title="API 接口任务"><Space wrap><TaskRunButton taskId="workflow_dry_run_check" type="primary">检查控制台链路</TaskRunButton><TaskRunButton taskId="list_latest_reports">刷新报告列表</TaskRunButton></Space></Section>
    <Section title="API 接口状态 / 已注册路由"><Table rowKey={(r)=>`${r.name}-${r.endpoint}`} size="small" dataSource={rows} columns={[{title:'接口',dataIndex:'name',width:220},{title:'Endpoint',dataIndex:'endpoint'},{title:'Method',dataIndex:'method',width:110},{title:'状态',dataIndex:'status',width:100,render:statusTag},{title:'来源',dataIndex:'source',width:300}]} scroll={{ x: 1200, y: 560 }} locale={{ emptyText: <EmptyState text="未读取到 API 路由状态。" /> }} /></Section>
  </div>;
}

export function SystemAuditPage() {
  const rows = useAsync(getSystemAuditRows, [] as AuditRow[]);
  return <div className="page-grid">
    <Section title="日志审计任务"><Space wrap><TaskRunButton taskId="workflow_dry_run_check" type="primary">生成链路审计</TaskRunButton><TaskRunButton taskId="list_latest_reports">刷新报告列表</TaskRunButton></Space></Section>
    <Section title="日志审计 / task_history"><Table rowKey={(r)=>`${r.runId}-${r.operation}`} size="small" dataSource={rows} columns={[{title:'时间',dataIndex:'time',width:200},{title:'用户',dataIndex:'user',width:120},{title:'模块',dataIndex:'module',width:110},{title:'操作',dataIndex:'operation',width:180},{title:'参数摘要',dataIndex:'paramsSummary'},{title:'IP',dataIndex:'ip',width:110},{title:'结果',dataIndex:'result',width:100,render:statusTag},{title:'来源',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1500, y: 560 }} locale={{ emptyText: <EmptyState text="暂无审计日志；运行任意任务后会写入持久化 task_history。" /> }} /></Section>
  </div>;
}

export function SystemAuthPage() {
  const rows = useAsync(getSystemPermissionRows, [] as PermissionRow[]);
  return <div className="page-grid">
    <Section title="权限管理说明" extra={<Tag color="green">基于任务白名单，不做虚假用户/角色数据</Tag>}><Typography.Paragraph>当前本地控制台没有接入多用户权限系统；真实权限边界来自后端任务白名单、dry-run-only、forbidden-in-live 和安全参数校验。</Typography.Paragraph></Section>
    <Section title="任务权限矩阵"><Table rowKey="id" size="small" dataSource={rows} columns={[{title:'任务ID',dataIndex:'id',width:240},{title:'名称',dataIndex:'name',width:180},{title:'分类',dataIndex:'category',width:110,render:(v)=><Tag color="blue">{v}</Tag>},{title:'safe_mode',dataIndex:'safeMode',width:100,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'dry_run_only',dataIndex:'dryRunOnly',width:120,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'requires_human_approval',dataIndex:'requiresHumanApproval',width:180,render:(v)=><Tag color={v?'gold':'green'}>{String(v)}</Tag>},{title:'forbidden_in_live',dataIndex:'forbiddenInLive',width:140,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'前端可运行',dataIndex:'canRunFromFrontend',width:110,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'产物',dataIndex:'outputArtifacts',render:(v:string[])=> (v || []).join(', ')},{title:'来源',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1800, y: 560 }} locale={{ emptyText: <EmptyState text="未读取到任务权限矩阵。" /> }} /></Section>
  </div>;
}
