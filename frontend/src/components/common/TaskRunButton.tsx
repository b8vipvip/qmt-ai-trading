import { Button, message } from 'antd';
import { useState } from 'react';
import type { ReactNode } from 'react';
import { runConsoleTask } from '../../services/taskService';

interface Props {
  taskId: string;
  params?: Record<string, unknown>;
  children: ReactNode;
  type?: 'primary' | 'default' | 'dashed' | 'link' | 'text';
  size?: 'small' | 'middle' | 'large';
}

export function TaskRunButton({ taskId, params, children, type, size = 'small' }: Props) {
  const [loading, setLoading] = useState(false);
  async function handleClick() {
    try {
      setLoading(true);
      const result = await runConsoleTask({ taskId, params });
      message.success(`${result.task?.task_name || taskId} ${result.task?.status || 'DONE'}`);
      window.dispatchEvent(new Event('qmt-task-finished'));
    } catch (error) {
      message.error(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }
  return <Button size={size} type={type} loading={loading} onClick={handleClick}>{children}</Button>;
}
