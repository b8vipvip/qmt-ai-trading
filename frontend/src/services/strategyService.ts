import { holdings, orders, strategies } from '../mock/mockData';
import { apiOrMock } from './apiClient';
import { mapOrderRows, mapStrategyStatusList } from './mappers';

export function getStrategyList() {
  return apiOrMock('/strategies/list', strategies, (body) => mapStrategyStatusList(body.data, strategies));
}

export async function getStrategyDetail(id: string) {
  const list = await getStrategyList();
  return {
    strategy: list.find((item) => item.id === id) ?? list[0] ?? strategies[0],
    holdings: holdings.slice(0, 12),
    rebalanceOrders: orders.slice(0, 8),
  };
}

export async function getRebalancePlan() {
  const backendOrders = await apiOrMock('/execution/orders', orders.slice(0, 10), (body) => mapOrderRows(body.data, orders.slice(0, 10)));
  return { holdings: holdings.slice(0, 16), orders: backendOrders, riskPassed: false, notice: '调仓计划只进入风控闸门，不直接下单。' };
}
