import { ExclamationCircleOutlined, MoonOutlined, SunOutlined } from '@ant-design/icons';
import { Button, Card, Empty, Input, Modal, Progress, Space, Tag, Tooltip, Typography } from 'antd';
import { useMemo, useState } from 'react';
import type { MetricItem, RiskLevel, StatusKind, SystemEvent } from '../../types';

const statusColor: Record<StatusKind, string> = { normal: 'success', warning: 'warning', danger: 'error', offline: 'default' };
const riskColor: Record<RiskLevel, string> = { LOW: 'green', MEDIUM: 'gold', HIGH: 'orange', CRITICAL: 'red' };

export function StatusBadge({ status, text }: { status: StatusKind; text?: string }) {
  return <Tag color={statusColor[status] ?? 'default'}>{text ?? String(status).toUpperCase()}</Tag>;
}

export function RiskLevelBadge({ level }: { level: RiskLevel }) {
  return <Tag color={riskColor[level] ?? 'default'}>{level}</Tag>;
}

export function SourcePathTag({ value }: { value?: string }) {
  if (!value) return <span className="muted">-</span>;
  return <Tooltip title={value}><Tag color="purple">artifact</Tag></Tooltip>;
}

export function EmptyState({ text = '暂无后端产物。请先运行对应任务，或等待真实接口接入。' }: { text?: string }) {
  return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={text} />;
}

export function MiniSparkline({ data }: { data: number[] }) {
  const safe = data.length ? data : [0, 0];
  const points = useMemo(() => {
    const max = Math.max(...safe);
    const min = Math.min(...safe);
    return safe.map((v, i) => `${(i / Math.max(1, safe.length - 1)) * 100},${28 - ((v - min) / Math.max(1, max - min)) * 24}`).join(' ');
  }, [safe]);
  return <svg className="sparkline" viewBox="0 0 100 32" preserveAspectRatio="none"><polyline points={points} fill="none" stroke="currentColor" strokeWidth="3" /></svg>;
}

export function MetricCard({ item }: { item: MetricItem }) {
  return <Card className={`metric-card ${item.status}`}><div className="metric-head"><span>{item.title}</span><StatusBadge status={item.status} /></div><div className="metric-value">{item.value}</div><div className="metric-foot"><span>{item.change}</span><MiniSparkline data={item.trend} /></div>{item.source && <SourcePathTag value={item.source} />}</Card>;
}

export function SystemStatusBar({ dark, onToggleTheme }: { dark: boolean; onToggleTheme: () => void }) {
  const now = new Date();
  return <div className="system-status-bar"><div className="status-title-line"><strong>控制台状态</strong><span>{now.toLocaleDateString()} {now.toLocaleTimeString()}</span></div><Space size={8}><Tag color="cyan">市场：非交易日</Tag><StatusBadge status="normal" text="行情连接" /><StatusBadge status="offline" text="券商未连接" /><StatusBadge status="normal" text="数据库正常" /><StatusBadge status="warning" text="风控 MEDIUM" /><Tag color="blue">模式：研究 / 仿真</Tag><Button size="small" icon={dark ? <SunOutlined /> : <MoonOutlined />} onClick={onToggleTheme}>{dark ? '浅色' : '深色'}</Button></Space></div>;
}

export function ConfirmDangerActionModal({ open, title, confirmText, onCancel, onConfirm }: { open: boolean; title: string; confirmText: string; onCancel: () => void; onConfirm: () => void }) {
  const [value, setValue] = useState('');
  const canConfirm = value === confirmText;
  return <Modal open={open} title={<Space><ExclamationCircleOutlined />{title}</Space>} onCancel={onCancel} footer={<Space><Button onClick={onCancel}>取消</Button><Button danger type="primary" disabled={!canConfirm} onClick={onConfirm}>确认</Button></Space>}><Typography.Paragraph type="danger">该动作属于高风险操作。当前版本仅完成界面保护与模拟回执。</Typography.Paragraph><Typography.Paragraph>请输入 <b>{confirmText}</b> 后才能继续。</Typography.Paragraph><Input value={value} onChange={(e) => setValue(e.target.value)} placeholder={confirmText} /></Modal>;
}

export function EventLogPanel({ events }: { events: SystemEvent[] }) {
  if (!events.length) return <EmptyState text="暂无系统事件；执行任务后会在这里显示 task_history 产物。" />;
  return <div className="event-log-panel">{events.map((e) => <div className="event-line" key={e.id}><span>{e.time}</span><StatusBadge status={e.level} text={e.module} /><p>{e.message}</p>{e.sourcePath && <SourcePathTag value={e.sourcePath} />}</div>)}</div>;
}

export function RiskGauge({ title, value }: { title: string; value: number }) {
  const status = value > 80 ? 'exception' : value > 55 ? 'active' : 'success';
  return <Card className="risk-gauge"><Typography.Text>{title}</Typography.Text><Progress percent={value} status={status as any} strokeLinecap="round" /></Card>;
}
