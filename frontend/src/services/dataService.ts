import { dataQuality, dataSources, dataTasks } from '../mock/mockData';
const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
export async function getDataSources() { await wait(); return dataSources; }
export async function getDataQualityRows() { await wait(); return dataQuality; }
export async function getDataTasks() { await wait(); return dataTasks; }
