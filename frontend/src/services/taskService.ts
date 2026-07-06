export interface RunTaskOptions {
  taskId: string;
  params?: Record<string, unknown>;
}

export interface TaskRunResult {
  ok: boolean;
  task?: {
    run_id: string;
    task_id: string;
    task_name: string;
    category: string;
    status: string;
    logs?: string[];
    output?: Record<string, unknown>;
    output_artifacts?: string[];
  };
  error?: string;
}

const SAFE_PARAMS: Record<string, unknown> = {
  dry_run: true,
  read_only: true,
};

export async function runConsoleTask({ taskId, params = {} }: RunTaskOptions): Promise<TaskRunResult> {
  const body = { task_id: taskId, params: { ...SAFE_PARAMS, ...params } };
  const response = await fetch('/api/v1/tasks/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `任务执行失败：${taskId}`);
  }
  return data;
}

export async function getTaskHistory(limit = 20) {
  const response = await fetch(`/api/v1/tasks/history?limit=${limit}`);
  return response.json();
}
