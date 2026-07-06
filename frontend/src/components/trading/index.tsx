import { Button, Space, Table, Tag, Timeline } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { BacktestTask, OrderRow, RiskRule, StrategyStatus } from '../../types';
import { EmptyState, RiskLevelBadge, SourcePathTag } from '../common';

export function StrategyStatusTable({ data, onDanger }: { data: StrategyStatus[]; onDanger?: (title: string) => void }) {
  const columns: ColumnsType<StrategyStatus> = [
    { title: '策略/产物名称', dataIndex: 'name', fixed: 'left', width: 220 },
    { title: '产物类型', dataIndex: 'type', width: 120 },
    { title: '模式', dataIndex: 'mode', width: 100, render: (v) => <Tag color="blue">{v}</Tag> },
    { title: '股票池/标的', dataIndex: 'pool', width: 120 },
    { title: '调仓/周期', dataIndex: 'rebalance', width: 110 },
    { title: '最新信号/动作', dataIndex: 'lastAction', width: 150, render: (v) => v ? <Tag color="cyan">{v}</Tag> : '-' },
    { title: '目标权重', dataIndex: 'targetWeight', width: 110, render: (v) => v ? `${v}` : '-' },
    { title: '今日收益', dataIndex: 'todayReturn', width: 110, render: (v) => <span className={v >= 0 ? 'up' : 'down'}>{v}%</span> },
    { title: '累计收益', dataIndex: 'totalReturn', width: 110, render: (v) => <span className={v >= 0 ? 'up' : 'down'}>{v}%</span> },
    { title: '最大回撤', dataIndex: 'maxDrawdown', width: 110, render: (v) => <span className="down">{v}%</span> },
    { title: '仓位/目标', dataIndex: 'position', width: 110, render: (v) => `${v}%` },
    { title: '信号数', dataIndex: 'signalCount', width: 80 },
    { title: '风控', dataIndex: 'riskStatus', width: 100, render: (v) => <RiskLevelBadge level={v} /> },
    { title: '状态', dataIndex: 'status', width: 110, render: (v) => <Tag color={v === 'RUNNING' ? 'green' : v === 'STOPPED' ? 'red' : 'gold'}>{v}</Tag> },
    { title: '来源', dataIndex: 'sourcePath', width: 120, render: (v) => <SourcePathTag value={v} /> },
    { title: '操作', fixed: 'right', width: 180, render: (_, row) => <Space><Button size="small">查看</Button><Button size="small">暂停</Button><Button danger size="small" onClick={() => onDanger?.(`停止策略：${row.name}`)}>停止</Button></Space> },
  ];
  return <Table rowKey="id" size="small" columns={columns} dataSource={data} scroll={{ x: 1800, y: 360 }} pagination={false} locale={{ emptyText: <EmptyState text="暂无策略信号产物；请运行 strategy_dry_run_signals。" /> }} />;
}

export function RiskRuleTable({ data, onDanger }: { data: RiskRule[]; onDanger: (title: string) => void }) {
  const columns: ColumnsType<RiskRule> = [
    { title: '规则名称', dataIndex: 'name', width: 180 },
    { title: '类型', dataIndex: 'type', width: 90 },
    { title: '阈值', dataIndex: 'threshold', width: 150 },
    { title: '当前值', dataIndex: 'current', width: 150 },
    { title: '动作', dataIndex: 'action', width: 110, render: (v) => <Tag color={['停止交易', '平仓', '拦截'].includes(v) ? 'red' : 'gold'}>{v}</Tag> },
    { title: '启用', dataIndex: 'enabled', width: 80, render: (v) => <Tag color={v ? 'green' : 'default'}>{String(v)}</Tag> },
    { title: '最近触发', dataIndex: 'lastTriggered', width: 150 },
    { title: '说明', dataIndex: 'description', width: 220, render: (v) => v || '-' },
    { title: '来源', dataIndex: 'sourcePath', width: 120, render: (v) => <SourcePathTag value={v} /> },
    { title: '操作', width: 180, render: (_, row) => <Space><Button size="small">编辑</Button><Button danger size="small" onClick={() => onDanger(`禁用风控规则：${row.name}`)}>禁用</Button></Space> },
  ];
  return <Table rowKey="id" size="small" columns={columns} dataSource={data} scroll={{ x: 1400, y: 390 }} pagination={false} locale={{ emptyText: <EmptyState text="暂无风控规则；安全策略未接入时仍由后端硬闸门保护。" /> }} />;
}

export function OrderStatusTimeline({ status }: { status: string }) {
  const states = ['CREATED', 'RISK_CHECKED', 'SENT', 'ACCEPTED', 'PARTIAL_FILLED', 'FILLED', 'CANCELLED', 'REJECTED', 'FAILED'];
  const previewStatus = String(status || '').startsWith('PREVIEW') ? 'RISK_CHECKED' : status;
  const idx = states.indexOf(previewStatus);
  return <Timeline items={states.slice(0, Math.max(1, idx + 1)).map((s) => ({ color: s === previewStatus ? 'blue' : 'green', children: s }))} />;
}

export function BacktestReportPanel({ task }: { task: BacktestTask }) {
  return <div className="report-summary"><Tag color="blue">{task.name}</Tag><Tag>股票池：{task.universe}</Tag><Tag>区间：{task.range}</Tag><Tag color="green">状态：{task.status}</Tag><SourcePathTag value={task.sourcePath} /><p>策略评价摘要：收益曲线平滑，最大回撤可控，超额收益主要来自因子暴露与行业轮动；需要继续验证小盘流动性与冲击成本。</p></div>;
}

export type { OrderRow };
