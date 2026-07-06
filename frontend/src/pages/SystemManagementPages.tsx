import { Button, Card, Col, Descriptions, Form, Input, Modal, Row, Select, Space, Switch, Table, Tag, Typography, message } from 'antd';
import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { EmptyState, SourcePathTag } from '../components/common';
import { TaskRunButton } from '../components/common/TaskRunButton';
import { getApiConfigs, getSystemApiRows, getSystemAuditRows, getSystemConfigRows, getSystemPermissionRows, getSystemSummary, saveApiConfig, testApiConfig } from '../services/systemManagementService';
import type { ApiConfigRow, ApiRow, AuditRow, ConfigRow, PermissionRow, SystemSummary } from '../services/systemManagementService';

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

function statusTag(value: string) {
  const text = String(value || 'UNKNOWN');
  const color = ['READY', 'SUCCESS', 'NORMAL', 'SAVED'].includes(text) ? 'green' : ['ERROR', 'FAILED'].includes(text) ? 'red' : 'gold';
  return <Tag color={color}>{text}</Tag>;
}

function metric(title: string, value: ReactNode) {
  return <Card className="metric-card"><b>{title}</b><div className="metric-value">{value}</div></Card>;
}

export function SystemConfigPage() {
  const summary = useAsync(getSystemSummary, { artifactRoot: '', taskCount: 0, historyCount: 0, latestRunAt: '', liveTradingEnabled: false, orderSubmitEnabled: false, orderCancelEnabled: false } as SystemSummary);
  const rows = useAsync(getSystemConfigRows, [] as ConfigRow[]);
  return <div className="page-grid">
    <Section title="配置中心说明" extra={<Tag color="green">只读真实配置</Tag>}><Typography.Paragraph>这里展示本地控制台运行配置和安全状态，不放无意义任务按钮；API 凭据请到“API 接口”页面维护。</Typography.Paragraph></Section>
    <Row gutter={[16,16]}><Col xs={12} md={6}>{metric('白名单任务', summary.taskCount)}</Col><Col xs={12} md={6}>{metric('任务历史', summary.historyCount)}</Col><Col xs={12} md={6}>{metric('发单开关', String(summary.orderSubmitEnabled))}</Col><Col xs={12} md={6}>{metric('实盘开关', String(summary.liveTradingEnabled))}</Col></Row>
    <Section title="配置中心 / 只读真实配置"><Table rowKey="key" size="small" dataSource={rows} columns={[{title:'配置键',dataIndex:'key',width:180},{title:'配置项',dataIndex:'name',width:180},{title:'当前值',dataIndex:'value',render:(v,r)=><Typography.Text code={r.sensitive}> {String(v || '-')} </Typography.Text>},{title:'可编辑',dataIndex:'editable',width:90,render:(v)=><Tag color={v?'gold':'green'}>{String(v)}</Tag>},{title:'敏感',dataIndex:'sensitive',width:80,render:(v)=><Tag color={v?'red':'green'}>{String(v)}</Tag>},{title:'来源',dataIndex:'source',width:240}]} scroll={{ x: 1100, y: 480 }} locale={{ emptyText: <EmptyState text="未读取到系统配置。" /> }} /></Section>
    <Section title="安全说明"><Descriptions bordered size="small" column={2} items={[{key:'1',label:'产物目录',children:summary.artifactRoot},{key:'2',label:'最新任务时间',children:summary.latestRunAt || '-'},{key:'3',label:'密钥展示策略',children:'不显示 .env/token/secret/key 明文；本地 API 配置文件已加入 .gitignore'},{key:'4',label:'交易安全',children:'orderSubmit/liveTrading 固定为 false'}]} /></Section>
  </div>;
}

export function SystemApiPage() {
  const rows = useAsync(getSystemApiRows, [] as ApiRow[]);
  const configs = useAsync(getApiConfigs, [] as ApiConfigRow[]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<ApiConfigRow | null>(null);
  const [form] = Form.useForm();

  const openForm = (row?: ApiConfigRow) => {
    setEditing(row || null);
    form.setFieldsValue(row || { provider: 'akshare', purpose: 'market', enabled: true });
    setOpen(true);
  };
  const submit = async () => {
    const values = await form.validateFields();
    await saveApiConfig({ ...editing, ...values });
    message.success('API 配置已保存');
    setOpen(false);
    window.dispatchEvent(new Event('qmt-api-config-saved'));
  };
  const test = async (id: string) => {
    const result = await testApiConfig(id);
    if (result.status === 'READY') message.success(result.message);
    else message.warning(result.message);
  };

  return <div className="page-grid">
    <Section title="外部数据 API 配置" extra={<Button type="primary" onClick={() => openForm()}>新增 API</Button>}>
      <Table rowKey="id" size="small" dataSource={configs} columns={[{title:'名称',dataIndex:'name',width:180},{title:'Provider',dataIndex:'provider',width:120,render:(v)=><Tag color="blue">{v}</Tag>},{title:'用途',dataIndex:'purpose',width:110},{title:'Base URL',dataIndex:'baseUrl'},{title:'账号',dataIndex:'account',width:120},{title:'Token',dataIndex:'tokenMasked',width:120,render:(v,r)=><Tag color={r.hasToken?'green':'default'}>{r.hasToken ? v : '未配置'}</Tag>},{title:'启用',dataIndex:'enabled',width:90,render:(v)=><Tag color={v?'green':'default'}>{String(v)}</Tag>},{title:'更新时间',dataIndex:'updatedAt',width:180},{title:'来源',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>},{title:'操作',width:180,render:(_,row)=><Space><Button size="small" onClick={()=>openForm(row)}>编辑</Button><Button size="small" onClick={()=>test(row.id)}>测试</Button></Space>}]} scroll={{ x: 1500, y: 360 }} locale={{ emptyText: <EmptyState text="暂无外部数据 API；点击“新增 API”配置 AkShare / Tushare / BaoStock / QMT。" /> }} />
    </Section>
    <Section title="本地控制台 API 状态"><Table rowKey={(r)=>`${r.name}-${r.endpoint}`} size="small" dataSource={rows} columns={[{title:'接口',dataIndex:'name',width:220},{title:'Endpoint',dataIndex:'endpoint'},{title:'Method',dataIndex:'method',width:110},{title:'状态',dataIndex:'status',width:100,render:statusTag},{title:'来源',dataIndex:'source',width:300}]} scroll={{ x: 1200, y: 360 }} locale={{ emptyText: <EmptyState text="未读取到 API 路由状态。" /> }} /></Section>
    <Modal open={open} onCancel={()=>setOpen(false)} onOk={submit} title={editing ? '编辑 API 配置' : '新增 API 配置'} destroyOnClose>
      <Form form={form} layout="vertical">
        <Form.Item name="id" label="配置ID"><Input placeholder="留空则自动使用 provider-purpose" disabled={!!editing} /></Form.Item>
        <Form.Item name="name" label="显示名称" rules={[{ required: true, message: '请输入显示名称' }]}><Input placeholder="例如：Tushare Pro 基本面" /></Form.Item>
        <Form.Item name="provider" label="Provider" rules={[{ required: true }]}><Select options={[{value:'akshare',label:'AkShare'}, {value:'tushare',label:'Tushare'}, {value:'baostock',label:'BaoStock'}, {value:'qmt_xtdata',label:'QMT xtdata'}, {value:'custom_http',label:'自定义 HTTP'}]} /></Form.Item>
        <Form.Item name="purpose" label="用途" rules={[{ required: true }]}><Select options={[{value:'market',label:'行情'}, {value:'fundamental',label:'基本面'}, {value:'news',label:'公告新闻'}, {value:'research',label:'研究'}, {value:'all',label:'全部'}]} /></Form.Item>
        <Form.Item name="baseUrl" label="Base URL"><Input placeholder="AkShare/BaoStock 可留空；自定义 HTTP 必填" /></Form.Item>
        <Form.Item name="account" label="账号/用户名"><Input /></Form.Item>
        <Form.Item name="token" label="Token / 密钥"><Input.Password placeholder="留空表示保留原 token；保存后只显示掩码" /></Form.Item>
        <Form.Item name="enabled" label="启用" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
      </Form>
    </Modal>
  </div>;
}

export function SystemAuditPage() {
  const rows = useAsync(getSystemAuditRows, [] as AuditRow[]);
  return <div className="page-grid">
    <Section title="日志审计说明"><Typography.Paragraph>日志审计只展示任务执行历史和参数摘要；运行日志不再作为全局底部组件出现在每个页面。</Typography.Paragraph></Section>
    <Section title="日志审计 / task_history"><Table rowKey={(r)=>`${r.runId}-${r.operation}`} size="small" dataSource={rows} columns={[{title:'时间',dataIndex:'time',width:200},{title:'用户',dataIndex:'user',width:120},{title:'模块',dataIndex:'module',width:110},{title:'操作',dataIndex:'operation',width:180},{title:'参数摘要',dataIndex:'paramsSummary'},{title:'IP',dataIndex:'ip',width:110},{title:'结果',dataIndex:'result',width:100,render:statusTag},{title:'来源',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1500, y: 560 }} locale={{ emptyText: <EmptyState text="暂无审计日志；运行任意任务后会写入持久化 task_history。" /> }} /></Section>
  </div>;
}

export function SystemAuthPage() {
  const rows = useAsync(getSystemPermissionRows, [] as PermissionRow[]);
  return <div className="page-grid">
    <Section title="权限管理说明" extra={<Tag color="green">基于任务白名单</Tag>}><Typography.Paragraph>当前本地控制台没有接入多用户权限系统；真实权限边界来自后端任务白名单、dry-run-only、forbidden-in-live 和安全参数校验。</Typography.Paragraph></Section>
    <Section title="任务权限矩阵"><Table rowKey="id" size="small" dataSource={rows} columns={[{title:'任务ID',dataIndex:'id',width:240},{title:'名称',dataIndex:'name',width:180},{title:'分类',dataIndex:'category',width:110,render:(v)=><Tag color="blue">{v}</Tag>},{title:'safe_mode',dataIndex:'safeMode',width:100,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'dry_run_only',dataIndex:'dryRunOnly',width:120,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'requires_human_approval',dataIndex:'requiresHumanApproval',width:180,render:(v)=><Tag color={v?'gold':'green'}>{String(v)}</Tag>},{title:'forbidden_in_live',dataIndex:'forbiddenInLive',width:140,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'前端可运行',dataIndex:'canRunFromFrontend',width:110,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'产物',dataIndex:'outputArtifacts',render:(v:string[])=> (v || []).join(', ')},{title:'来源',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1800, y: 560 }} locale={{ emptyText: <EmptyState text="未读取到任务权限矩阵。" /> }} /></Section>
  </div>;
}
