import { holdings, orders, trades } from '../mock/mockData';
import { apiOrMock, postMockAction } from './apiClient';
import { mapHoldingRows, mapOrderRows } from './mappers';

export function getTargetHoldings() {
  return apiOrMock('/execution/holdings', holdings, (body) => mapHoldingRows(body.data, holdings));
}

export function getOrderList() {
  return apiOrMock('/execution/orders', orders, (body) => mapOrderRows(body.data, orders));
}

export function getTradeList() {
  return apiOrMock('/execution/trades', trades);
}

export function previewOrderAction(orderId: string) {
  return postMockAction('/actions/order-preview', { orderId });
}
