# A股量化交易控制台 Frontend

这是新版前端操作台，定位为专业量化交易控制台，不替代现有 `local_console_app`，当前阶段先完成 React + TypeScript + Vite + Ant Design + ECharts 的 UI、页面结构、Mock 数据与 service 适配层。

## 启动

```powershell
cd D:\AI\qmt\frontend
npm install
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:5173/dashboard
```

## 构建

```powershell
cd D:\AI\qmt\frontend
npm run build
npm run preview
```

## 目录说明

```text
src/
  app/          路由与整体布局
  components/   通用组件、图表组件、交易/风控组件
  pages/        Dashboard、DataCenter、Factors、Strategies、Backtest、Deployment、Execution、Risk、Monitoring、Settings
  services/     接口适配层，当前返回 mock，后续替换真实 API
  mock/         mock 数据
  types/        TypeScript 类型
  styles/       全局样式
```

## Mock 数据

当前所有页面均从 `src/services/*.ts` 读取 mock 数据，数据源位于 `src/mock/mockData.ts`。包含策略、持仓、订单、成交、风控事件、因子、回测任务、系统日志、资产曲线等。

## 后续接真实 API

UI 页面不直接读取 mock。后续只需要在 `src/services/` 中把 mock 返回改为 `fetch('/api/v1/...')`，即可复用现有页面和组件。

## 安全说明

交易执行、风控中心、实盘过渡中的高风险按钮都带二次确认。当前阶段只做 mock，不连接真实交易执行接口。
