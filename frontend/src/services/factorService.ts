import { equityCurve, factors } from '../mock/mockData';
import { apiOrMock } from './apiClient';
import { mapFactorRows } from './mappers';

export function getFactorList() {
  return apiOrMock('/factors/list', factors, (body) => mapFactorRows(body.data, factors));
}

export async function getFactorDetail(id: string) {
  const list = await getFactorList();
  return {
    factor: list.find((item) => item.id === id) ?? list[0] ?? factors[0],
    icSeries: equityCurve.slice(-90),
    decays: [1, .82, .64, .51, .39, .28],
    layers: [2.1, 1.4, .7, -.2, -1.1],
  };
}
