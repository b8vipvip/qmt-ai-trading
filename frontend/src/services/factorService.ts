import { equityCurve, factors } from '../mock/mockData';
const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
export async function getFactorList() { await wait(); return factors; }
export async function getFactorDetail(id: string) { await wait(); return { factor: factors.find((item) => item.id === id) ?? factors[0], icSeries: equityCurve.slice(-90), decays: [1, .82, .64, .51, .39, .28], layers: [2.1, 1.4, .7, -.2, -1.1] }; }
