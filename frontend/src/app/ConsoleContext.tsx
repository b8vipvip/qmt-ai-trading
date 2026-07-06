import { createContext, useContext } from 'react';

export interface ConsoleContextValue {
  themeMode: 'dark' | 'light';
  tradeMode: '研究' | '仿真';
  readonly: boolean;
  dryRun: boolean;
}

export const ConsoleContext = createContext<ConsoleContextValue>({
  themeMode: 'dark',
  tradeMode: '研究',
  readonly: true,
  dryRun: true,
});

export function useConsoleContext() {
  return useContext(ConsoleContext);
}
