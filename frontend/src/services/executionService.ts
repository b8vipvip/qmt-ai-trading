import { holdings, orders, trades } from '../mock/mockData';
import { apiOrMock, postMockAction } from './apiClient';

export function getTargetHoldings() {
  return apiOrMock('/execution/holdings', holdings);
}

export function getOrderList() {
  return apiOrMock('/execution/orders', orders);
}

export function getTradeList() {
  return apiOrMock('/execution/trades', trades);
}

export function previewOrderAction(orderId: string) {
  return postMockAction('/actions/order-preview', { orderId });
}
