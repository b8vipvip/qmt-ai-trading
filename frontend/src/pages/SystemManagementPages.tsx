import { AutoComplete, Button, Card, Col, Form, Input, InputNumber, Modal, Row, Select, Space, Switch, Table, Tag, Typography, message } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { EmptyState, SourcePathTag } from '../components/common';
import { getApiConfigs, getSystemApiRows, getSystemAuditRows, getSystemPermissionRows, getSystemSettings, getSystemSummary, saveApiConfig, saveApiConfigPurposes, saveSystemSettings, scanQmtPaths, settingsFallback, testApiConfig, testQmtSettings } from '../services/systemManagementService';
import type { ApiConfigRow, ApiRow, AuditRow, PermissionRow, QmtPathCandidate, SystemSettings, SystemSummary } from '../services/systemManagementService';

function useAsync<T>(loader: () => Promise<T>, fallback: T): T {
  const [data, setData] = useState<T>(fallback);
  useEffect(() => {
    let mounted = true;
    const load = () => loader().then((v) => { if (mounted) setData(v); }).catch(() => { if (mounted) setData(fallback); });
    load();
    window.addEventListener('qmt-task-finished', load);
    window.addEventListener('qmt-api-config-saved', load);
    window.addEventListener('qmt-settings-saved', load);
    return () => { mounted = false; window.removeEventListener('qmt-task-finished', load); window.removeEventListener('qmt-api-config-saved', load); window.removeEventListener('qmt-settings-saved', load); };
  }, []);
  return data;
}

function Section({ title, extra, children }: { title: string; extra?: ReactNode; children: ReactNode }) { return <Card className="section-card" title={title} extra={extra}>{children}</Card>; }
function statusTag(value: string) { const text = String(value || 'UNKNOWN'); const color = ['READY', 'SUCCESS', 'NORMAL', 'SAVED'].includes(text) ? 'green' : ['ERROR', 'FAILED'].includes(text) ? 'red' : 'gold'; return <Tag color={color}>{text}</Tag>; }
function metric(title: string, value: ReactNode) { return <Card className="metric-card"><b>{title}</b><div className="metric-value">{value}</div></Card>; }

const purposeOptions = [
  { value: 'market', label: '行情' }, { value: 'fundamental', label: '基本面' }, { value: 'news', label: '公告新闻' },
  { value: 'research', label: '研究' }, { value: 'ai', label: 'AI服务' }, { value: 'all', label: '全部' },
];

export function SystemConfigPage() {
  const summary = useAsync(getSystemSummary, { artifactRoot: '', taskCount: 0, historyCount: 0, apiConfigCount: 0, enabledApiConfigCount: 0, latestRunAt: '', runMode: 'research', qmtPathConfigured: false, liveTradingEnabled: false, orderSubmitEnabled: false, orderCancelEnabled: false } as SystemSummary);
  const settings = useAsync(getSystemSettings, settingsFallback);
  const configs = useAsync(getApiConfigs, [] as ApiConfigRow[]);
  const [form] = Form.useForm<SystemSettings>();
  const [saving, setSaving] = useState(false);
  useEffect(() => { form.setFieldsValue(settings); }, [settings, form]);
  const apiConfigs = configs.filter((x) => x.provider !== 'qmt_xtdata');

  const save = async () => { try { setSaving(true); await saveSystemSettings(form.getFieldsValue(true) as SystemSettings); message.success('系统配置已保存'); window.dispatchEvent(new Event('qmt-settings-saved')); } catch (error) { message.error(error instanceof Error ? error.message : String(error)); } finally { setSaving(false); } };
  const savePurposes = async (id: string, purposes: string[]) => { try { await saveApiConfigPurposes(id, purposes); message.success('API 用途已保存'); window.dispatchEvent(new Event('qmt-api-config-saved')); } catch (error) { message.error(error instanceof Error ? error.message : String(error)); } };

  return <div className="page-grid">
    <Row gutter={[16,16]}><Col xs={12} md={6}>{metric('运行模式', summary.runMode)}</Col><Col xs={12} md={6}>{metric('API配置', summary.apiConfigCount)}</Col><Col xs={12} md={6}>{metric('QMT路径', summary.qmtPathConfigured ? '已配置' : '未配置')}</Col><Col xs={12} md={6}>{metric('实盘开关', String(summary.liveTradingEnabled))}</Col></Row>
    <Form form={form} layout="vertical">
      <Section title="系统运行模式" extra={<Button type="primary" loading={saving} onClick={save}>保存配置</Button>}>
        <Row gutter={16}><Col xs={24} md={8}><Form.Item name={['runtime','mode']} label="运行模式"><Select options={[{value:'research',label:'研究'}, {value:'simulation',label:'仿真'}, {value:'shadow_live',label:'影子实盘'}, {value:'small_capital_live',label:'小资金实盘'}, {value:'full_live',label:'正式实盘'}]} /></Form.Item></Col><Col xs={24} md={16}><Typography.Text type="secondary">运行模式是系统级参数，不会自动触发下单。真实下单和撤单仍由后端安全闸门锁定。</Typography.Text></Col></Row>
      </Section>
      <Section title="默认交易参数">
        <Row gutter={16}><Col xs={24} md={6}><Form.Item name={['trading','defaultStockPool']} label="默认股票池"><Input /></Form.Item></Col><Col xs={24} md={6}><Form.Item name={['trading','commissionRate']} label="默认手续费"><InputNumber style={{width:'100%'}} min={0} max={0.02} step={0.00001} /></Form.Item></Col><Col xs={24} md={6}><Form.Item name={['trading','slippageBps']} label="默认滑点 bps"><InputNumber style={{width:'100%'}} min={0} max={500} /></Form.Item></Col><Col xs={24} md={6}><Form.Item name={['trading','rebalancePeriod']} label="默认调仓周期"><Select options={[{value:'daily',label:'每日'}, {value:'weekly',label:'每周'}, {value:'monthly',label:'每月'}, {value:'manual',label:'手动'}]} /></Form.Item></Col></Row>
        <Row gutter={16}><Col xs={24} md={6}><Form.Item name={['trading','backtestInitialCash']} label="回测初始资金"><InputNumber style={{width:'100%'}} min={1000} /></Form.Item></Col><Col xs={24} md={6}><Form.Item name={['trading','backtestStartDate']} label="回测开始日期"><Input /></Form.Item></Col><Col xs={24} md={6}><Form.Item name={['trading','backtestEndDate']} label="回测结束日期"><Input placeholder="留空表示最新" /></Form.Item></Col><Col xs={24} md={6}><Form.Item name={['trading','stampTaxRate']} label="印花税"><InputNumber style={{width:'100%'}} min={0} max={0.02} step={0.0001} /></Form.Item></Col></Row>
        <Row gutter={16}><Col xs={12} md={6}><Form.Item name={['trading','enableT1']} label="启用 T+1" valuePropName="checked"><Switch /></Form.Item></Col><Col xs={12} md={6}><Form.Item name={['trading','enableLimitCheck']} label="涨跌停限制" valuePropName="checked"><Switch /></Form.Item></Col><Col xs={12} md={6}><Form.Item name={['trading','enableSuspensionCheck']} label="停牌检测" valuePropName="checked"><Switch /></Form.Item></Col><Col xs={12} md={6}><Form.Item name={['trading','enableLiquidityLimit']} label="流动性限制" valuePropName="checked"><Switch /></Form.Item></Col></Row>
      </Section>
      <Section title="风控默认参数">
        <Row gutter={16}><Col xs={24} md={5}><Form.Item name={['risk','maxPositionPct']} label="最大仓位 %"><InputNumber style={{width:'100%'}} min={0} max={100} /></Form.Item></Col><Col xs={24} md={5}><Form.Item name={['risk','maxSinglePositionPct']} label="单票上限 %"><InputNumber style={{width:'100%'}} min={0} max={100} /></Form.Item></Col><Col xs={24} md={5}><Form.Item name={['risk','maxIndustryExposurePct']} label="行业上限 %"><InputNumber style={{width:'100%'}} min={0} max={100} /></Form.Item></Col><Col xs={24} md={5}><Form.Item name={['risk','maxDrawdownPct']} label="最大回撤阈值 %"><InputNumber style={{width:'100%'}} min={0} max={100} /></Form.Item></Col><Col xs={24} md={4}><Form.Item name={['risk','dailyLossLimitPct']} label="日内亏损阈值 %"><InputNumber style={{width:'100%'}} min={0} max={100} /></Form.Item></Col></Row>
      </Section>
      <Section title="数据路径"><Row gutter={16}><Col xs={24} md={12}><Form.Item name={['paths','marketCacheDir']} label="行情缓存目录"><Input /></Form.Item></Col><Col xs={24} md={12}><Form.Item name={['paths','factorArtifactDir']} label="因子产物目录"><Input /></Form.Item></Col><Col xs={24} md={12}><Form.Item name={['paths','backtestReportDir']} label="回测报告目录"><Input /></Form.Item></Col><Col xs={24} md={12}><Form.Item name={['paths','taskHistoryDir']} label="任务历史目录"><Input /></Form.Item></Col></Row></Section>
      <Section title="安全开关"><Row gutter={16}><Col xs={12} md={6}><Form.Item name={['safety','allowRealOrder']} label="允许真实下单" valuePropName="checked"><Switch disabled /></Form.Item></Col><Col xs={12} md={6}><Form.Item name={['safety','allowCancelOrder']} label="允许撤单" valuePropName="checked"><Switch disabled /></Form.Item></Col><Col xs={12} md={6}><Form.Item name={['safety','allowAccountQuery']} label="允许查询账户" valuePropName="checked"><Switch /></Form.Item></Col><Col xs={12} md={6}><Form.Item name={['safety','enableHumanApproval']} label="启用人工审批" valuePropName="checked"><Switch disabled /></Form.Item></Col></Row><Typography.Text type="secondary">真实下单、撤单和关闭人工审批当前被安全策略锁定，不能在前端打开；账户查询只影响只读账户任务。</Typography.Text></Section>
    </Form>
    <Section title="API 用途配置" extra={<Tag color="blue">API 接口页只维护接口信息，这里决定用途</Tag>}><Table rowKey="id" size="small" dataSource={apiConfigs} columns={[{title:'API名称',dataIndex:'name',width:180},{title:'Provider',dataIndex:'provider',width:140,render:(v)=><Tag color="blue">{v}</Tag>},{title:'启用',dataIndex:'enabled',width:90,render:(v)=><Tag color={v?'green':'default'}>{String(v)}</Tag>},{title:'用途',dataIndex:'purposes',render:(v:string[],row)=><Select mode="multiple" allowClear style={{minWidth:360}} value={v || []} options={purposeOptions} onChange={(values)=>savePurposes(row.id, values)} />},{title:'来源',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1000 }} locale={{ emptyText: <EmptyState text="暂无 API 配置；请先到 API 接口页面新增接口。" /> }} /></Section>
  </div>;
}

export function SystemApiPage() {
  const rows = useAsync(getSystemApiRows, [] as ApiRow[]);
  const configs = useAsync(getApiConfigs, [] as ApiConfigRow[]);
  const settings = useAsync(getSystemSettings, settingsFallback);
  const apiConfigs = configs.filter((x) => x.provider !== 'qmt_xtdata');
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<ApiConfigRow | null>(null);
  const [form] = Form.useForm();
  const [qmtForm] = Form.useForm<SystemSettings['qmt']>();
  const [qmtCandidates, setQmtCandidates] = useState<QmtPathCandidate[]>([]);
  const [qmtBusy, setQmtBusy] = useState(false);
  useEffect(() => { qmtForm.setFieldsValue(settings.qmt); }, [settings, qmtForm]);
  const qmtPathOptions = useMemo(() => qmtCandidates.filter((x)=>x.kind==='qmt_path').map((x)=>({ value:x.path, label:`${x.path}${x.exists?'':'（未确认）'}` })), [qmtCandidates]);
  const xtquantOptions = useMemo(() => qmtCandidates.filter((x)=>x.kind==='xtquant_python_path').map((x)=>({ value:x.path, label:x.path })), [qmtCandidates]);
  const candidateByPath = (path: string) => qmtCandidates.find((x)=>x.path === path);

  const openForm = (row?: ApiConfigRow) => { setEditing(row || null); form.setFieldsValue(row ? { ...row, token: '' } : { provider: 'openai_compatible', enabled: true }); setOpen(true); };
  const submit = async () => { const values = await form.validateFields(); await saveApiConfig({ ...editing, ...values }); message.success('API 配置已保存'); setOpen(false); window.dispatchEvent(new Event('qmt-api-config-saved')); };
  const test = async (id: string) => { const result = await testApiConfig(id); if (result.status === 'READY') message.success(result.message); else message.warning(result.message); };
  const saveQmt = async () => { const qmt = qmtForm.getFieldsValue(true); await saveSystemSettings({ ...settings, qmt }); message.success('QMT / xtdata 路径已保存'); window.dispatchEvent(new Event('qmt-settings-saved')); };
  const scanQmt = async () => { try { setQmtBusy(true); const result = await scanQmtPaths(); setQmtCandidates(result.candidates || []); const qmt = (result.candidates || []).find((x)=>x.kind==='qmt_path' && x.exists) || (result.candidates || []).find((x)=>x.kind==='qmt_path'); const xt = (result.candidates || []).find((x)=>x.kind==='xtquant_python_path' && x.exists); if (qmt) qmtForm.setFieldsValue({ xtdataPath: qmt.path, clientName: qmt.clientName }); if (xt) qmtForm.setFieldsValue({ xtquantPythonPath: xt.path }); message.success(`扫描完成，发现 ${result.count} 个候选路径`); } catch (error) { message.error(error instanceof Error ? error.message : String(error)); } finally { setQmtBusy(false); } };
  const testQmt = async () => { try { setQmtBusy(true); await saveQmt(); const res = await testQmtSettings(); if (res.status === 'READY') message.success(res.message); else message.warning(`${res.message}；路径状态：${res.pathStatus}`); } catch (error) { message.error(error instanceof Error ? error.message : String(error)); } finally { setQmtBusy(false); } };

  return <div className="page-grid">
    <Section title="QMT / xtdata 本地路径" extra={<Space><Button loading={qmtBusy} onClick={scanQmt}>自动扫描路径</Button><Button type="primary" loading={qmtBusy} onClick={testQmt}>保存并测试 QMT 连接</Button></Space>}>
      <Form form={qmtForm} layout="vertical"><Row gutter={16}><Col xs={24} md={8}><Form.Item name="clientName" label="客户端名称"><Input placeholder="选择路径后自动识别，例如 国金证券 QMT" /></Form.Item></Col><Col xs={24} md={16}><Form.Item name="xtdataPath" label="QMT / xtdata 路径"><AutoComplete options={qmtPathOptions} onSelect={(value)=>{ const c = candidateByPath(value); if (c) qmtForm.setFieldsValue({ clientName: c.clientName }); }} placeholder="点自动扫描后从候选路径选择；也可手动修正" /></Form.Item></Col></Row><Row gutter={16}><Col xs={24}><Form.Item name="xtquantPythonPath" label="xtquant Python 路径"><AutoComplete options={xtquantOptions} placeholder="可选：点自动扫描后选择 xtquant 所在目录" /></Form.Item></Col></Row></Form>
      <div className="artifact-list"><b>已配置路径</b><span>客户端：{settings.qmt.clientName || '-'}</span><span>QMT / xtdata：{settings.qmt.xtdataPath || '未配置'}</span><span>xtquant Python：{settings.qmt.xtquantPythonPath || '未配置'}</span></div>
    </Section>
    <Section title="外部 API / AI 服务接口配置" extra={<Button type="primary" onClick={() => openForm()}>新增 API</Button>}>
      <Table rowKey="id" size="small" dataSource={apiConfigs} columns={[{title:'名称',dataIndex:'name',width:180},{title:'Provider',dataIndex:'provider',width:150,render:(v)=><Tag color="blue">{v}</Tag>},{title:'Base URL',dataIndex:'baseUrl',width:260},{title:'默认模型',dataIndex:'modelName',width:160},{title:'账号',dataIndex:'account',width:120},{title:'Token',dataIndex:'tokenMasked',width:120,render:(v,r)=><Tag color={r.hasToken?'green':'default'}>{r.hasToken ? v : '未配置'}</Tag>},{title:'用途',dataIndex:'purposes',width:180,render:(v:string[])=>(v || []).length ? (v || []).map((x)=><Tag key={x}>{x}</Tag>) : <Tag>未分配</Tag>},{title:'启用',dataIndex:'enabled',width:90,render:(v)=><Tag color={v?'green':'default'}>{String(v)}</Tag>},{title:'更新时间',dataIndex:'updatedAt',width:180},{title:'来源',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>},{title:'操作',width:180,render:(_,row)=><Space><Button size="small" onClick={()=>openForm(row)}>编辑</Button><Button size="small" onClick={()=>test(row.id)}>测试</Button></Space>}]} scroll={{ x: 1750, y: 430 }} locale={{ emptyText: <EmptyState text="暂无 API；点击“新增 API”配置 AI 接口、AkShare、Tushare、BaoStock 或自定义 HTTP。" /> }} />
    </Section>
    <Section title="本地控制台 API 状态"><Table rowKey={(r)=>`${r.name}-${r.endpoint}`} size="small" dataSource={rows} columns={[{title:'接口',dataIndex:'name',width:220},{title:'Endpoint',dataIndex:'endpoint'},{title:'Method',dataIndex:'method',width:110},{title:'状态',dataIndex:'status',width:100,render:statusTag},{title:'来源',dataIndex:'source',width:300}]} scroll={{ x: 1200, y: 360 }} locale={{ emptyText: <EmptyState text="未读取到 API 路由状态。" /> }} /></Section>
    <Modal open={open} onCancel={()=>setOpen(false)} onOk={submit} title={editing ? '编辑 API 配置' : '新增 API 配置'} destroyOnClose>
      <Form form={form} layout="vertical"><Form.Item name="id" label="配置ID"><Input placeholder="留空则自动生成" disabled={!!editing} /></Form.Item><Form.Item name="name" label="显示名称" rules={[{ required: true, message: '请输入显示名称' }]}><Input placeholder="例如：OpenAI 兼容接口 / Tushare Pro / AkShare" /></Form.Item><Form.Item name="provider" label="Provider" rules={[{ required: true }]}><Select options={[{value:'openai_compatible',label:'AI接口（OpenAI兼容）'}, {value:'akshare',label:'AkShare'}, {value:'tushare',label:'Tushare'}, {value:'baostock',label:'BaoStock'}, {value:'custom_http',label:'自定义 HTTP'}]} /></Form.Item><Form.Item name="baseUrl" label="Base URL"><Input placeholder="AI接口/自定义HTTP填写，例如 https://api.openai.com/v1；AkShare 可留空" /></Form.Item><Form.Item name="modelName" label="默认模型"><Input placeholder="AI接口建议填写，例如 gpt-4o / deepseek-chat；用于 /models 被禁用时测试 chat/completions" /></Form.Item><Form.Item name="account" label="账号/用户名"><Input /></Form.Item><Form.Item name="token" label="Token / API Key"><Input.Password placeholder="留空表示保留原 token；保存后只显示掩码" /></Form.Item><Form.Item name="enabled" label="启用" valuePropName="checked"><Switch /></Form.Item><Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item></Form>
    </Modal>
  </div>;
}

export function SystemAuditPage() {
  const rows = useAsync(getSystemAuditRows, [] as AuditRow[]);
  return <div className="page-grid"><Section title="日志审计 / task_history"><Table rowKey={(r)=>`${r.runId}-${r.operation}`} size="small" dataSource={rows} columns={[{title:'时间',dataIndex:'time',width:200},{title:'用户',dataIndex:'user',width:120},{title:'模块',dataIndex:'module',width:110},{title:'操作',dataIndex:'operation',width:180},{title:'参数摘要',dataIndex:'paramsSummary'},{title:'IP',dataIndex:'ip',width:110},{title:'结果',dataIndex:'result',width:100,render:statusTag},{title:'来源',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1500, y: 620 }} locale={{ emptyText: <EmptyState text="暂无审计日志；运行任意任务后会写入持久化 task_history。" /> }} /></Section></div>;
}

export function SystemAuthPage() {
  const rows = useAsync(getSystemPermissionRows, [] as PermissionRow[]);
  return <div className="page-grid"><Section title="权限管理说明" extra={<Tag color="green">基于任务白名单</Tag>}><Typography.Paragraph>当前本地控制台没有接入多用户权限系统；真实权限边界来自后端任务白名单、dry-run-only、forbidden-in-live 和安全参数校验。</Typography.Paragraph></Section><Section title="任务权限矩阵"><Table rowKey="id" size="small" dataSource={rows} columns={[{title:'任务ID',dataIndex:'id',width:240},{title:'名称',dataIndex:'name',width:180},{title:'分类',dataIndex:'category',width:110,render:(v)=><Tag color="blue">{v}</Tag>},{title:'safe_mode',dataIndex:'safeMode',width:100,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'dry_run_only',dataIndex:'dryRunOnly',width:120,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'requires_human_approval',dataIndex:'requiresHumanApproval',width:180,render:(v)=><Tag color={v?'gold':'green'}>{String(v)}</Tag>},{title:'forbidden_in_live',dataIndex:'forbiddenInLive',width:140,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'前端可运行',dataIndex:'canRunFromFrontend',width:110,render:(v)=><Tag color={v?'green':'red'}>{String(v)}</Tag>},{title:'产物',dataIndex:'outputArtifacts',render:(v:string[])=> (v || []).join(', ')},{title:'来源',dataIndex:'sourcePath',width:120,render:(v)=><SourcePathTag value={v}/>}]} scroll={{ x: 1800, y: 560 }} locale={{ emptyText: <EmptyState text="未读取到任务权限矩阵。" /> }} /></Section></div>;
}
