import { deploymentStages } from '../mock/mockData';
const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
export async function getDeploymentStages() { await wait(); return deploymentStages; }
