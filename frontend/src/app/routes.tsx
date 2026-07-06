import {
  BarChartOutlined,
  BuildOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  DeploymentUnitOutlined,
  ExperimentOutlined,
  RadarChartOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  StockOutlined,
} from '@ant-design/icons';
import { BacktestPage, DashboardPage, DataCenterPage, DeploymentPage, ExecutionPage, FactorsPage, MonitoringPage, RiskCenterPage, SettingsPage, StrategiesPage } from '../pages';
import { FundamentalDataPage, NewsDataPage, DataQualityPage, DataTasksPage } from '../pages/DataSubPages';
import { MarketDataPage } from '../pages/MarketDataPage';

export interface AppRoute {
  path: string;
  label: string;
  element: JSX.Element;
  icon?: JSX.Element;
  children?: AppRoute[];
}

export const routes: AppRoute[] = [
  { path: '/dashboard', label: '总览仪表盘', icon: <DashboardOutlined />, element: <DashboardPage /> },
  { path: '/data', label: '数据中心', icon: <DatabaseOutlined />, element: <MarketDataPage />, children: [
    { path: '/data/market', label: '行情数据', element: <MarketDataPage /> }, { path: '/data/fundamental', label: '基本面数据', element: <FundamentalDataPage /> }, { path: '/data/news', label: '公告新闻', element: <NewsDataPage /> }, { path: '/data/quality', label: '数据质量', element: <DataQualityPage /> }, { path: '/data/tasks', label: '数据任务', element: <DataTasksPage /> },
  ] },
  { path: '/factors', label: '因子研究', icon: <ExperimentOutlined />, element: <FactorsPage />, children: [
    { path: '/factors/library', label: '因子库', element: <FactorsPage /> }, { path: '/factors/calc', label: '因子计算', element: <FactorsPage /> }, { path: '/factors/ic', label: 'IC 分析', element: <FactorsPage /> }, { path: '/factors/layer', label: '分层收益', element: <FactorsPage /> }, { path: '/factors/combo', label: '因子组合', element: <FactorsPage /> },
  ] },
  { path: '/strategies', label: '策略中心', icon: <BuildOutlined />, element: <StrategiesPage />, children: [
    { path: '/strategies/list', label: '策略列表', element: <StrategiesPage /> }, { path: '/strategies/editor', label: '策略编辑', element: <StrategiesPage /> }, { path: '/strategies/pool', label: '股票池管理', element: <StrategiesPage /> }, { path: '/strategies/portfolio', label: '组合构建', element: <StrategiesPage /> }, { path: '/strategies/rebalance', label: '调仓计划', element: <StrategiesPage /> },
  ] },
  { path: '/backtest', label: '回测验证', icon: <BarChartOutlined />, element: <BacktestPage />, children: [
    { path: '/backtest/tasks', label: '回测任务', element: <BacktestPage /> }, { path: '/backtest/reports', label: '回测报告', element: <BacktestPage /> }, { path: '/backtest/robustness', label: '稳健性检验', element: <BacktestPage /> }, { path: '/backtest/optimize', label: '参数寻优', element: <BacktestPage /> },
  ] },
  { path: '/deployment', label: '实盘过渡', icon: <DeploymentUnitOutlined />, element: <DeploymentPage />, children: [
    { path: '/deployment/paper', label: 'Paper Trading', element: <DeploymentPage /> }, { path: '/deployment/shadow', label: 'Shadow Trading', element: <DeploymentPage /> }, { path: '/deployment/small', label: 'Small Capital', element: <DeploymentPage /> }, { path: '/deployment/live', label: 'Full Live', element: <DeploymentPage /> },
  ] },
  { path: '/execution', label: '交易执行', icon: <StockOutlined />, element: <ExecutionPage />, children: [
    { path: '/execution/targets', label: '目标持仓', element: <ExecutionPage /> }, { path: '/execution/plans', label: '订单计划', element: <ExecutionPage /> }, { path: '/execution/orders', label: '订单管理', element: <ExecutionPage /> }, { path: '/execution/trades', label: '成交记录', element: <ExecutionPage /> }, { path: '/execution/broker', label: '券商接口', element: <ExecutionPage /> },
  ] },
  { path: '/risk', label: '风控中心', icon: <SafetyCertificateOutlined />, element: <RiskCenterPage />, children: [
    { path: '/risk/overview', label: '风控总览', element: <RiskCenterPage /> }, { path: '/risk/pretrade', label: '交易前风控', element: <RiskCenterPage /> }, { path: '/risk/intraday', label: '交易中风控', element: <RiskCenterPage /> }, { path: '/risk/post', label: '事后风控', element: <RiskCenterPage /> }, { path: '/risk/rules', label: '风控规则', element: <RiskCenterPage /> }, { path: '/risk/breakers', label: '熔断记录', element: <RiskCenterPage /> },
  ] },
  { path: '/monitoring', label: '监控复盘', icon: <RadarChartOutlined />, element: <MonitoringPage />, children: [
    { path: '/monitoring/realtime', label: '实时监控', element: <MonitoringPage /> }, { path: '/monitoring/attribution', label: '收益归因', element: <MonitoringPage /> }, { path: '/monitoring/execution-quality', label: '成交质量', element: <MonitoringPage /> }, { path: '/monitoring/decay', label: '策略失效检测', element: <MonitoringPage /> }, { path: '/monitoring/daily-review', label: '每日复盘', element: <MonitoringPage /> },
  ] },
  { path: '/settings', label: '系统管理', icon: <SettingOutlined />, element: <SettingsPage />, children: [
    { path: '/settings/config', label: '配置中心', element: <SettingsPage /> }, { path: '/settings/api', label: 'API 接口', element: <SettingsPage /> }, { path: '/settings/audit', label: '日志审计', element: <SettingsPage /> }, { path: '/settings/auth', label: '权限管理', element: <SettingsPage /> },
  ] },
];

export const flatRoutes = routes.flatMap((route) => [route, ...(route.children ?? [])]);
export function getRouteByPath(path: string) {
  return flatRoutes.find((route) => route.path === path) ?? routes[0];
}
