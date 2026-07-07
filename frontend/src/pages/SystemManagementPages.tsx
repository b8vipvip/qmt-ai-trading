import { AutoComplete, Button, Card, Col, Form, Input, InputNumber, Modal, Row, Select, Space, Switch, Table, Tag, Typography, message } from 'antd';
import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { EmptyState, SourcePathTag } from '../components/common';
import { getApiConfigs, getSystemAuditRows, getSystemPermissionRows, getSystemSettings, getSystemSummary, saveApiConfig, saveApiConfigPurposes, saveSystemSettings, scanQmtPaths, settingsFallback, testApiConfig, testQmtSettings } from '../services/systemManagementService';
import type { ApiConfigRow, AuditRow, PermissionRow, QmtPathCandidate, QmtTestResult, SystemSettings, SystemSummary } from '../services/systemManagementService';

type QmtPathKey = 'qmtClientPath' | 'xtdataPath' | 'xtquantPythonPath';
type SystemPathKey = keyof SystemSettings['paths'];

type QmtClientRow = {
  kind: 'qmtClientPath';
  label: string;
  path: string;
  clientName: string;
  status: string;
  message: string;
};

function useAsync<T>(loader: () => Promise<T>, fallback: T): T {
  const [data, setData] = useState<T>(fallback);
  useEffect(() => {
    let mounted = true;
    const load = () => loader().then((v) => { if (mounted) setData(v); }).catch(() => { if (mounted) setData(fallback); });
    load();
    window.addEventListener('qmt-task-finished', load);
    window.addEventListener('qmt-api-config-saved', load);
    window.addEventListener('qmt-settings-saved', load);
    return () => {
      mounted = false;
      window.removeEventListener('qmt-task-finished', load);
      window.removeEventListener('qmt-api-config-saved', load);
      window.removeEventListener('qmt-settings-saved', load);
    };
  }, []);
  return data;
}

function Section({ title, extra, children }: { title: ReactNode; extra?: ReactNode; children: ReactNode }) {
  return <Card className="section-card" title={title} extra={extra}>{children}</Card>;
}

function statusTag(value: string) {
  const text = String(value || 'UNKNOWN');
  const color = ['READY', 'SUCCESS', 'NORMAL', 'SAVED', 'EXISTS', '已保存'].includes(text) ? 'green' : ['ERROR', 'FAILED', 'MISSING'].includes(text) ? 'red' : 'gold';
  return <Tag color={color}>{text}</Tag>;
}

function metric(title: string, value: ReactNode) {
  return <Card className="metric-card"><b>{title}</b><div className="metric-value">{value}</div></Card>;
}

function currentPathText(value?: string) {
  return <Typography.Text type="secondary">当前路径：{value || '未配置'}</Typography.Text>;
}

const purposeOptions = [
  { value: 'market', label: '行情' },
  { value: 'fundamental', label: '基本面' },
  { value: 'news', label: '公告新闻' },
  { value: 'research', label: '研究' },
  { value: 'ai', label: 'AI服务' },
  { value: 'all', label: '全部' },
];

const pathMeta: Record<QmtPathKey, { title: string; placeholder: string; scanText: string }> = {
  qmtClientPath: { title: 'QMT 客户端目录', placeholder: '建议选择 QMT 根目录或 bin.x64，例如 D:\\国金证券QMT交易端\\bin.x64', scanText: '扫描QMT目录' },
  xtdataPath: { title: 'xtdata 数据目录', placeholder: '建议选择 userdata_mini\\datadir；不要选普通程序 data 目录', scanText: '扫描xtdata目录' },
  xtquantPythonPath: { title: 'xtquant Python 目录', placeholder: '例如 C:\\Users\\...\\Python310\\Lib\\site-packages\\xtquant', scanText: '扫描xtquant目录' },
};

const systemPathMeta: { key: SystemPathKey; title: string; placeholder: string }[] = [
  { key: 'marketCacheDir', title: '行情缓存目录', placeholder: '例如 artifacts/reports/console/datahub' },
  { key: 'factorArtifactDir', title: '因子产物目录', placeholder: '例如 artifacts/reports/console/research' },
  { key: 'backtestReportDir', title: '回测报告目录', placeholder: '例如 artifacts/reports/console/backtest' },
  { key: 'taskHistoryDir', title: '任务历史目录', placeholder: '例如 artifacts/reports/console/task_history' },
];

export function SystemConfigPage() {
  const summary = useAsync(getSystemSummary, { artifactRoot: '', taskCount: 0, historyCount: 0, apiConfigCount: 0, enabledApiConfigCount: 0, latestRunAt: '', runMode: 'research', qmtPathConfigured: false, liveTradingEnabled: false, orderSubmitEnabled: false, orderCancelEnabled: false } as SystemSummary);
  const settings = useAsync(getSystemSettings, settingsFallback);
  const configs = useAsync(getApiConfigs, [] as ApiConfigRow[]);
  const [form] = Form.useForm<SystemSettings>();
  const [saving, setSaving] = useState(false);
  useEffect(() => { form.setFieldsValue(settings); }, [settings, form]);
  const apiConfigs = configs.filter((x) => x.provider !== 'qmt_xtdata');

  const save = async () => {
    try {
      setSaving(true);
      await saveSystemSettings(form.getFieldsValue(true) as SystemSettings);
      message.success('系统配置已保存');
      window.dispatchEvent(new Event('qmt-settings-saved'));
    } catch (error) {
      message.error(error instanceof Error ? error.message : String(error));
    } finally {
      setSaving(false);
    }
  };

  const savePurposes = async (id: string, purposes: string[]) => {
    try {
      await saveApiConfigPurposes(id, purposes);
      message.success('API 用途已保存');
      window.dispatchEvent(new Event('qmt-api-config-saved'));
    } catch (error) {
      message.error(error instanceof Error ? error.message : String(error));
    }
  };

  return <div className="page-grid">
    <Row gutter={[16, 16]}>
      <Col xs={12} md={6}>{metric('运行模式', summary.runMode)}</Col>
      <Col xs={12} md={6}>{metric('API配置', summary.apiConfigCount)}</Col>
      <Col xs={12} md={6}>{metric('QMT路径', summary.qmtPathConfigured ? '已配置' : '未配置')}</Col>
      <Col xs={12} md={6}>{metric('实盘开关', String(summary.liveTradingEnabled))}</Col>
    </Row>
    <Form form={form} layout="vertical">
      <Section title="系统运行模式" extra={<Button type="primary" loading={saving} onClick={save}>保存配置</Button>}>
        <Row gutter={16}>
          <Col xs={24} md={8}><Form.Item name={['runtime', 'mode']} label="运行模式"><Select options={[{ value: 'research', label: '研究' }, { value: 'simulation', label: '仿真' }, { value: 'shadow_live', label: '影子实盘' }, { value: 'small_capital_live', label: '小资金实盘' }, { value: 'full_live', label: '正式实盘' }]} /></Form.Item></Col>
          <Col xs={24} md={16}><Typography.Text type="secondary">运行模式是系统级参数，不会自动触发下单。真实下单和撤单仍由后端安全闸门锁定。</Typography.Text></Col>
        </Row>
      </Section>
      <Section title="默认交易参数">
        <Row gutter={16}>
          <Col xs={24} md={6}><Form.Item name={['trading', 'defaultStockPool']} label="默认股票池"><Input /></Form.Item></Col>
          <Col xs={24} md={6}><Form.Item name={['trading', 'commissionRate']} label="默认手续费"><InputNumber style={{ width: '100%' }} min={0} max={0.02} step={0.00001} /></Form.Item></Col>
          <Col xs={24} md={6}><Form.Item name={['trading', 'slippageBps']} label="默认滑点 bps"><InputNumber style={{ width: '100%' }} min={0} max={500} /></Form.Item></Col>
          <Col xs={24} md={6}><Form.Item name={['trading', 'rebalancePeriod']} label="默认调仓周期"><Select options={[{ value: 'daily', label: '每日' }, { value: 'weekly', label: '每周' }, { value: 'monthly', label: '每月' }, { value: 'manual', label: '手动' }]} /></Form.Item></Col>
          <Col xs={24} md={6}><Form.Item name={['trading', 'backtestInitialCash']} label="回测初始资金"><InputNumber style={{ width: '100%' }} min={1000} /></Form.Item></Col>
          <Col xs={24} md={6}><Form.Item name={['trading', 'backtestStartDate']} label="回测开始日期"><Input /></Form.Item></Col>
          <Col xs={24} md={6}><Form.Item name={['trading', 'backtestEndDate']} label="回测结束日期"><Input placeholder="留空表示最新" /></Form.Item></Col>
          <Col xs={24} md={6}><Form.Item name={['trading', 'stampTaxRate']} label="印花税"><InputNumber style={{ width: '100%' }} min={0} max={0.02} step={0.0001} /></Form.Item></Col>
          <Col xs={12} md={6}><Form.Item name={['trading', 'enableT1']} label="启用 T+1" valuePropName="checked"><Switch /></Form.Item></Col>
          <Col xs={12} md={6}><Form.Item name={['trading', 'enableLimitCheck']} label="涨跌停限制" valuePropName="checked"><Switch /></Form.Item></Col>
          <Col xs={12} md={6}><Form.Item name={['trading', 'enableSuspensionCheck']} label="停牌检测" valuePropName="checked"><Switch /></Form.Item></Col>
          <Col xs={12} md={6}><Form.Item name={['trading', 'enableLiquidityLimit']} label="流动性限制" valuePropName="checked"><Switch /></Form.Item></Col>
        </Row>
      </Section>
      <Section title="风控默认参数">
        <Row gutter={16}>
          <Col xs={24} md={5}><Form.Item name={['risk', 'maxPositionPct']} label="最大仓位 %"><InputNumber style={{ width: '100%' }} min={0} max={100} /></Form.Item></Col>
          <Col xs={24} md={5}><Form.Item name={['risk', 'maxSinglePositionPct']} label="单票上限 %"><InputNumber style={{ width: '100%' }} min={0} max={100} /></Form.Item></Col>
          <Col xs={24} md={5}><Form.Item name={['risk', 'maxIndustryExposurePct']} label="行业上限 %"><InputNumber style={{ width: '100%' }} min={0} max={100} /></Form.Item></Col>
          <Col xs={24} md={5}><Form.Item name={['risk', 'maxDrawdownPct']} label="最大回撤阈值 %"><InputNumber style={{ width: '100%' }} min={0} max={100} /></Form.Item></Col>
          <Col xs={24} md={4}><Form.Item name={['risk', 'dailyLossLimitPct']} label="日内亏损阈值 %"><InputNumber style={{ width: '100%' }} min={0} max={100} /></Form.Item></Col>
        </Row>
      </Section>
      <Section title="数据路径"><Row gutter={16}><Col xs={24} md={12}><Form.Item name={['paths', 'marketCacheDir']} label="行情缓存目录"><Input /></Form.Item></Col><Col xs={24} md={12}><Form.Item name={['paths', 'factorArtifactDir']} label="因子产物目录"><Input /></Form.Item></Col><Col xs={24} md={12}><Form.Item name={['paths', 'backtestReportDir']} label="回测报告目录"><Input /></Form.Item></Col><Col xs={24} md={12}><Form.Item name={['paths', 'taskHistoryDir']} label="任务历史目录"><Input /></Form.Item></Col></Row></Section>
      <Section title="安全开关"><Row gutter={16}><Col xs={12} md={6}><Form.Item name={['safety', 'allowRealOrder']} label="允许真实下单" valuePropName="checked"><Switch disabled /></Form.Item></Col><Col xs={12} md={6}><Form.Item name={['safety', 'allowCancelOrder']} label="允许撤单" valuePropName="checked"><Switch disabled /></Form.Item></Col><Col xs={12} md={6}><Form.Item name={['safety', 'allowAccountQuery']} label="允许查询账户" valuePropName="checked"><Switch /></Form.Item></Col><Col xs={12} md={6}><Form.Item name={['safety', 'enableHumanApproval']} label="启用人工审批" valuePropName="checked"><Switch disabled /></Form.Item></Col></Row><Typography.Text type="secondary">真实下单、撤单和关闭人工审批当前被安全策略锁定，不能在前端打开；账户查询只影响只读账户任务。</Typography.Text></Section>
    </Form>
    <Section title="API 用途配置" extra={<Tag color="blue">API 接口页只维护接口信息，这里决定用途</Tag>}>
      <Table rowKey="id" size="small" dataSource={apiConfigs} columns={[{ title: 'API名称', dataIndex: 'name', width: 180 }, { title: 'Provider', dataIndex: 'provider', width: 140, render: (v) => <Tag color="blue">{v}</Tag> }, { title: '启用', dataIndex: 'enabled', width: 90, render: (v) => <Tag color={v ? 'green' : 'default'}>{String(v)}</Tag> }, { title: '用途', dataIndex: 'purposes', render: (v: string[], row) => <Select mode="multiple" allowClear style={{ minWidth: 360 }} value={v || []} options={purposeOptions} onChange={(values) => savePurposes(row.id, values)} /> }, { title: '来源', dataIndex: 'sourcePath', width: 120, render: (v) => <SourcePathTag value={v} /> }]} scroll={{ x: 1000 }} locale={{ emptyText: <EmptyState text="暂无 API 配置；请先到 API 接口页面新增接口。" /> }} />
    </Section>
  </div>;
}

export function SystemApiPage() {
  const configs = useAsync(getApiConfigs, [] as ApiConfigRow[]);
  const settings = useAsync(getSystemSettings, settingsFallback);
  const apiConfigs = configs.filter((x) => x.provider !== 'qmt_xtdata');
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<ApiConfigRow | null>(null);
  const [form] = Form.useForm();
  const [qmtForm] = Form.useForm<SystemSettings['qmt']>();
  const [qmtCandidates, setQmtCandidates] = useState<QmtPathCandidate[]>([]);
  const [qmtBusy, setQmtBusy] = useState<QmtPathKey | 'loginApi' | ''>('');
  const [qmtTestResults, setQmtTestResults] = useState<Record<string, QmtTestResult>>({});
  const [pathDraft, setPathDraft] = useState<SystemSettings['paths']>(settingsFallback.paths);

  useEffect(() => { qmtForm.setFieldsValue(settings.qmt); }, [settings, qmtForm]);
  useEffect(() => { setPathDraft(settings.paths); }, [settings.paths]);

  const openForm = (row?: ApiConfigRow) => {
    setEditing(row || null);
    form.setFieldsValue(row ? { ...row, token: '' } : { provider: 'openai_compatible', enabled: true });
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

  const saveQmt = async (kind?: QmtPathKey) => {
    const qmt = qmtForm.getFieldsValue(true);
    await saveSystemSettings({ ...settings, qmt });
    message.success(kind ? `${pathMeta[kind].title} 已保存` : 'QMT 路径已保存');
    window.dispatchEvent(new Event('qmt-settings-saved'));
  };

  const saveSystemPath = async (key: SystemPathKey) => {
    await saveSystemSettings({ ...settings, paths: { ...settings.paths, ...pathDraft } });
    message.success(`${systemPathMeta.find((x) => x.key === key)?.title || '系统路径'} 已保存`);
    window.dispatchEvent(new Event('qmt-settings-saved'));
  };

  const scanQmt = async (kind: QmtPathKey) => {
    try {
      setQmtBusy(kind);
      const result = await scanQmtPaths(kind);
      setQmtCandidates((prev) => [...result.candidates, ...prev].filter((x, i, arr) => arr.findIndex((y) => y.kind === x.kind && y.path === x.path) === i));
      const first = (result.candidates || []).find((x) => x.kind === kind && x.exists) || (result.candidates || []).find((x) => x.kind === kind);
      if (first) qmtForm.setFieldsValue({ [kind]: first.path, clientName: first.clientName } as any);
      message.success(`扫描完成，发现 ${result.count} 个候选路径`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : String(error));
    } finally {
      setQmtBusy('');
    }
  };

  const testQmt = async () => {
    try {
      setQmtBusy('qmtClientPath');
      await saveQmt('qmtClientPath');
      const res = await testQmtSettings('qmtClientPath');
      setQmtTestResults((prev) => ({ ...prev, qmtClientPath: res }));
      if (res.status === 'READY') message.success('QMT 客户端测试通过');
      else message.warning(res.message);
    } catch (error) {
      message.error(error instanceof Error ? error.message : String(error));
    } finally {
      setQmtBusy('');
    }
  };

  const testLoggedInApi = async () => {
    try {
      setQmtBusy('loginApi');
      await saveQmt();
      const res = await testQmtSettings('loginApi');
      setQmtTestResults((prev) => ({ ...prev, loginApi: res }));
      if (res.status === 'READY') message.success('登录后 xtdata API 测试通过');
      else message.warning(res.message);
    } catch (error) {
      message.error(error instanceof Error ? error.message : String(error));
    } finally {
      setQmtBusy('');
    }
  };

  const optionsFor = (kind: QmtPathKey) => qmtCandidates.filter((x) => x.kind === kind).map((x) => ({ value: x.path, label: `${x.path}${x.exists ? '' : '（未确认）'}` }));
  const candidateByPath = (kind: QmtPathKey, path: string) => qmtCandidates.find((x) => x.kind === kind && x.path === path);

  const qmtPathField = (kind: QmtPathKey, withClientActions = false) => <Form.Item name={kind} label={pathMeta[kind].title} style={{ maxWidth: 1120 }}>
    <Space.Compact style={{ width: '100%' }}>
      <AutoComplete
        style={{ width: '100%' }}
        options={optionsFor(kind)}
        onSelect={(value) => {
          const c = candidateByPath(kind, value);
          if (c) qmtForm.setFieldsValue({ clientName: c.clientName });
        }}
      >
        <Input placeholder={pathMeta[kind].placeholder} />
      </AutoComplete>
      <Button type="primary" loading={qmtBusy === kind} onClick={() => scanQmt(kind)}>选择/扫描</Button>
      <Button loading={qmtBusy === kind} onClick={() => scanQmt(kind)}>{pathMeta[kind].scanText}</Button>
      <Button onClick={() => saveQmt(kind)}>保存</Button>
    </Space.Compact>
    <div style={{ marginTop: 6 }}>{currentPathText((settings.qmt as any)[kind])}</div>
    {withClientActions && <Typography.Text type="secondary">客户端测试只针对 QMT 启动程序；xtdata 和 xtquant 目录不放入客户端列表。</Typography.Text>}
  </Form.Item>;

  const systemPathField = ({ key, title, placeholder }: { key: SystemPathKey; title: string; placeholder: string }) => <Form.Item label={title} style={{ maxWidth: 720 }}>
    <Space.Compact style={{ width: '100%' }}>
      <Input value={pathDraft[key] || ''} placeholder={placeholder} onChange={(event) => setPathDraft((prev) => ({ ...prev, [key]: event.target.value }))} />
      <Button onClick={() => saveSystemPath(key)}>保存</Button>
    </Space.Compact>
    <div style={{ marginTop: 6 }}>{currentPathText(settings.paths[key])}</div>
  </Form.Item>;

  const loginApiMessage = qmtTestResults.loginApi?.message || '';
  const clientRow: QmtClientRow = {
    kind: 'qmtClientPath',
    label: 'QMT客户端',
    path: settings.qmt.qmtClientPath || '',
    clientName: settings.qmt.clientName || '-',
    status: qmtTestResults.qmtClientPath?.status || (settings.qmt.qmtClientPath ? '已保存' : '未配置'),
    message: `${qmtTestResults.qmtClientPath?.message || ''}${loginApiMessage ? `${qmtTestResults.qmtClientPath?.message ? '；' : ''}登录后API：${loginApiMessage}` : ''}`,
  };

  const apiColumns = [
    { title: '名称', dataIndex: 'name', width: 150 },
    { title: 'Provider', dataIndex: 'provider', width: 125, render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: 'Base URL', dataIndex: 'baseUrl', width: 230, ellipsis: true },
    { title: '模型', dataIndex: 'modelName', width: 110 },
    { title: '账号', dataIndex: 'account', width: 90 },
    { title: 'Token', dataIndex: 'tokenMasked', width: 105, render: (v: string, r: ApiConfigRow) => <Tag color={r.hasToken ? 'green' : 'default'}>{r.hasToken ? v : '未配置'}</Tag> },
    { title: '用途', dataIndex: 'purposes', width: 130, render: (v: string[]) => (v || []).length ? (v || []).map((x) => <Tag key={x}>{x}</Tag>) : <Tag>未分配</Tag> },
    { title: '启用', dataIndex: 'enabled', width: 80, render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{String(v)}</Tag> },
    { title: '更新时间', dataIndex: 'updatedAt', width: 170 },
    { title: '来源', dataIndex: 'sourcePath', width: 95, render: (v: string) => <SourcePathTag value={v} /> },
    { title: '操作', width: 135, fixed: 'right' as const, render: (_: unknown, row: ApiConfigRow) => <Space size={4}><Button size="small" onClick={() => openForm(row)}>编辑</Button><Button size="small" onClick={() => test(row.id)}>测试</Button></Space> },
  ];

  return <div className="page-grid">
    <Section title="QMT 客户端与 xtdata / xtquant 路径">
      <Form form={qmtForm} layout="vertical">
        <Form.Item name="clientName" hidden><Input /></Form.Item>
        {qmtPathField('qmtClientPath', true)}
        {qmtPathField('xtdataPath')}
        {qmtPathField('xtquantPythonPath')}
      </Form>
      <Table
        rowKey="kind"
        size="small"
        dataSource={[clientRow]}
        pagination={false}
        columns={[
          { title: '类型', dataIndex: 'label', width: 120 },
          { title: '识别客户端', dataIndex: 'clientName', width: 125 },
          { title: '客户端路径', dataIndex: 'path', width: 390, ellipsis: true, render: (v) => <Typography.Text copyable={!!v}>{v || '未配置'}</Typography.Text> },
          { title: '状态', dataIndex: 'status', width: 90, render: statusTag },
          { title: '测试信息', dataIndex: 'message', ellipsis: true },
          { title: '操作', width: 230, fixed: 'right', render: () => <Space size={4}><Button size="small" onClick={() => saveQmt('qmtClientPath')}>保存</Button><Button size="small" loading={qmtBusy === 'qmtClientPath'} onClick={testQmt}>测试连接</Button><Button size="small" loading={qmtBusy === 'loginApi'} onClick={testLoggedInApi}>登录后API</Button></Space> },
        ]}
        scroll={{ x: 1040 }}
      />
    </Section>

    <Section title="系统目录 / .env 目录统一配置">
      <Row gutter={16}>
        {systemPathMeta.map((item) => <Col xs={24} xl={12} key={item.key}>{systemPathField(item)}</Col>)}
      </Row>
    </Section>

    <Section title={<Space size={12}><span>外部 API / AI 服务接口配置</span><Button type="primary" size="small" onClick={() => openForm()}>新增 API</Button></Space>}>
      <Table rowKey="id" size="small" dataSource={apiConfigs} columns={apiColumns as any} scroll={{ x: 1420, y: 360 }} locale={{ emptyText: <EmptyState text="暂无 API；点击“新增 API”配置 AI 接口、AkShare、Tushare、BaoStock 或自定义 HTTP。" /> }} />
    </Section>

    <Modal open={open} onCancel={() => setOpen(false)} onOk={submit} title={editing ? '编辑 API 配置' : '新增 API 配置'} destroyOnClose>
      <Form form={form} layout="vertical">
        <Form.Item name="id" label="配置ID"><Input placeholder="留空则自动生成" disabled={!!editing} /></Form.Item>
        <Form.Item name="name" label="显示名称" rules={[{ required: true, message: '请输入显示名称' }]}><Input placeholder="例如：OpenAI 兼容接口 / Tushare Pro / AkShare" /></Form.Item>
        <Form.Item name="provider" label="Provider" rules={[{ required: true }]}><Select options={[{ value: 'openai_compatible', label: 'AI接口（OpenAI兼容）' }, { value: 'akshare', label: 'AkShare' }, { value: 'tushare', label: 'Tushare' }, { value: 'baostock', label: 'BaoStock' }, { value: 'custom_http', label: '自定义 HTTP' }]} /></Form.Item>
        <Form.Item name="baseUrl" label="Base URL"><Input placeholder="AI接口/自定义HTTP填写，例如 https://api.openai.com/v1；AkShare 可留空" /></Form.Item>
        <Form.Item name="modelName" label="默认模型"><Input placeholder="AI接口建议填写，例如 gpt-4o / deepseek-chat；用于 /models 被禁用时测试 chat/completions" /></Form.Item>
        <Form.Item name="account" label="账号/用户名"><Input /></Form.Item>
        <Form.Item name="token" label="Token / API Key"><Input.Password placeholder="留空表示保留原 token；保存后只显示掩码" /></Form.Item>
        <Form.Item name="enabled" label="启用" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
      </Form>
    </Modal>
  </div>;
}

export function SystemAuditPage() {
  const rows = useAsync(getSystemAuditRows, [] as AuditRow[]);
  return <div className="page-grid"><Section title="日志审计 / task_history"><Table rowKey={(r) => `${r.runId}-${r.operation}`} size="small" dataSource={rows} columns={[{ title: '时间', dataIndex: 'time', width: 200 }, { title: '用户', dataIndex: 'user', width: 120 }, { title: '模块', dataIndex: 'module', width: 110 }, { title: '操作', dataIndex: 'operation', width: 180 }, { title: '参数摘要', dataIndex: 'paramsSummary' }, { title: 'IP', dataIndex: 'ip', width: 110 }, { title: '结果', dataIndex: 'result', width: 100, render: statusTag }, { title: '来源', dataIndex: 'sourcePath', width: 120, render: (v) => <SourcePathTag value={v} /> }]} scroll={{ x: 1500, y: 620 }} locale={{ emptyText: <EmptyState text="暂无审计日志；运行任意任务后会写入持久化 task_history。" /> }} /></Section></div>;
}

export function SystemAuthPage() {
  const rows = useAsync(getSystemPermissionRows, [] as PermissionRow[]);
  return <div className="page-grid"><Section title="权限管理说明" extra={<Tag color="green">基于任务白名单</Tag>}><Typography.Paragraph>当前本地控制台没有接入多用户权限系统；真实权限边界来自后端任务白名单、dry-run-only、forbidden-in-live 和安全参数校验。</Typography.Paragraph></Section><Section title="任务权限矩阵"><Table rowKey="id" size="small" dataSource={rows} columns={[{ title: '任务ID', dataIndex: 'id', width: 240 }, { title: '名称', dataIndex: 'name', width: 180 }, { title: '分类', dataIndex: 'category', width: 110, render: (v) => <Tag color="blue">{v}</Tag> }, { title: 'safe_mode', dataIndex: 'safeMode', width: 100, render: (v) => <Tag color={v ? 'green' : 'red'}>{String(v)}</Tag> }, { title: 'dry_run_only', dataIndex: 'dryRunOnly', width: 120, render: (v) => <Tag color={v ? 'green' : 'red'}>{String(v)}</Tag> }, { title: 'requires_human_approval', dataIndex: 'requiresHumanApproval', width: 180, render: (v) => <Tag color={v ? 'gold' : 'green'}>{String(v)}</Tag> }, { title: 'forbidden_in_live', dataIndex: 'forbiddenInLive', width: 140, render: (v) => <Tag color={v ? 'green' : 'red'}>{String(v)}</Tag> }, { title: '前端可运行', dataIndex: 'canRunFromFrontend', width: 110, render: (v) => <Tag color={v ? 'green' : 'red'}>{String(v)}</Tag> }, { title: '产物', dataIndex: 'outputArtifacts', render: (v: string[]) => (v || []).join(', ') }, { title: '来源', dataIndex: 'sourcePath', width: 120, render: (v) => <SourcePathTag value={v} /> }]} scroll={{ x: 1800, y: 560 }} locale={{ emptyText: <EmptyState text="未读取到任务权限矩阵。" /> }} /></Section></div>;
}
