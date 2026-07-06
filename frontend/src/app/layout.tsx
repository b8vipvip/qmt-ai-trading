import { BellOutlined, MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { Button, ConfigProvider, Drawer, Layout, Menu, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useEffect, useMemo, useState } from 'react';
import { EventLogPanel, SystemStatusBar } from '../components/common';
import { systemEvents } from '../mock/mockData';
import { flatRoutes, getRouteByPath, routes } from './routes';

const { Header, Sider, Content, Footer } = Layout;

function toMenuItems() {
  return routes.map((route) => ({
    key: route.path,
    icon: route.icon,
    label: route.label,
    children: route.children?.map((child) => ({ key: child.path, label: child.label })),
  }));
}

export function AppLayout() {
  const [dark, setDark] = useState(true);
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [path, setPath] = useState(window.location.pathname === '/' ? '/dashboard' : window.location.pathname);
  const activeRoute = getRouteByPath(path);
  const openKeys = useMemo(() => routes.filter((r) => r.children?.some((c) => c.path === path)).map((r) => r.path), [path]);

  useEffect(() => {
    const onPop = () => setPath(window.location.pathname === '/' ? '/dashboard' : window.location.pathname);
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const go = (key: string) => {
    const route = flatRoutes.find((item) => item.path === key) ?? routes[0];
    window.history.pushState(null, '', route.path);
    setPath(route.path);
  };

  return <ConfigProvider locale={zhCN} theme={{ algorithm: dark ? theme.darkAlgorithm : theme.defaultAlgorithm, token: { colorPrimary: '#2f81f7', borderRadius: 12, fontSize: 13 } }}>
    <Layout className={`quant-shell ${dark ? 'dark' : 'light'}`}>
      <Sider className="quant-sider" collapsible collapsed={collapsed} trigger={null} width={288}>
        <div className="brand"><b>{collapsed ? 'QMT' : 'A股量化控制台'}</b><span>{!collapsed && 'Data → Alpha → Risk → Execution'}</span></div>
        <Menu mode="inline" selectedKeys={[path]} defaultOpenKeys={openKeys} items={toMenuItems()} onClick={(info) => go(info.key)} />
      </Sider>
      <Layout>
        <Header className="quant-header"><Button type="text" icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={() => setCollapsed(!collapsed)} /><SystemStatusBar dark={dark} onToggleTheme={() => setDark(!dark)} /><Button icon={<BellOutlined />} onClick={() => setDrawerOpen(true)}>告警</Button></Header>
        <Content className="quant-content"><div className="page-title"><div><h1>{activeRoute.label}</h1><p>专业量化交易工作台：当前阶段为前端 UI、Mock 数据与接口适配层，不触发真实交易动作。</p></div></div>{activeRoute.element}</Content>
        <Footer className="event-footer"><details><summary>运行日志 / 系统事件流</summary><EventLogPanel events={systemEvents.slice(0, 8)} /></details></Footer>
      </Layout>
      <Drawer title="风险告警 / 通知中心" open={drawerOpen} onClose={() => setDrawerOpen(false)} width={420}><EventLogPanel events={systemEvents} /></Drawer>
    </Layout>
  </ConfigProvider>;
}
