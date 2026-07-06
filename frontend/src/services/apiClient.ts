export interface ApiEnvelope<T> {
  ok?: boolean;
  status?: string;
  source?: string;
  data?: T;
  error?: string;
}

const API_PREFIX = '/api/v1/frontend';

function isUseful<T>(value: T, fallback: T): boolean {
  if (Array.isArray(fallback)) return Array.isArray(value) && value.length > 0;
  if (value && typeof value === 'object') return Object.keys(value as Record<string, unknown>).length > 0;
  return value !== undefined && value !== null;
}

export async function apiOrMock<T>(path: string, fallback: T, picker?: (body: ApiEnvelope<T> | any) => T): Promise<T> {
  try {
    const response = await fetch(`${API_PREFIX}${path}`);
    if (!response.ok) return fallback;
    const body = await response.json();
    const picked = picker ? picker(body) : (body.data as T);
    return isUseful(picked, fallback) ? picked : fallback;
  } catch {
    return fallback;
  }
}

export async function postMockAction(path: string, body: Record<string, unknown>) {
  try {
    const response = await fetch(`${API_PREFIX}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return response.ok ? response.json() : { ok: true, dryRun: true, message: '本地模拟操作已拦截真实交易。' };
  } catch {
    return { ok: true, dryRun: true, message: '本地模拟操作已拦截真实交易。' };
  }
}
