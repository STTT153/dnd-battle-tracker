import { createContext, useContext, type ReactNode } from 'react';
import type { CommandRegistry } from './registry';

const Context = createContext<CommandRegistry | null>(null);

export function CommandProvider({ registry, children }: {
  registry: CommandRegistry; children: ReactNode;
}) {
  return <Context.Provider value={registry}>{children}</Context.Provider>;
}

export function useCommands() {
  const registry = useContext(Context);
  if (!registry) throw new Error('缺少 CommandProvider');
  return registry;
}
