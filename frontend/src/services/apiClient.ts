export interface ApiEnvelope<T> {
  ok?: boolean;
  status?: string;
  source?: string;
  data?: T;
  error?: string;
}

const API_PREFIX = '/api/v1/frontend';

function hasDataField(body: unknown): body is { data: unknown } {
  return !!body && typeof body === 'object' && Object.prototype.hasOwnProperty.call(body, 'data');
}

export async function apiOrMock<T>(path: string, fallback: T, picker?: (body: ApiEnvelope<T> | any) => T): Promise<T> {
  try {
    const response = await fetch(`${API_PREFIX}${path}`);
    if (!response.ok) return fallback;
    const body = await response.json();
    if (body?.ok === false) return fallback;
    const picked = picker ? picker(body) : (hasDataField(body) ? body.data as T : undefined);
    return picked === undefined || picked === null ? fallback : picked;
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
