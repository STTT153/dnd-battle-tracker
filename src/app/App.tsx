import { CommandProvider } from '../commands/CommandProvider';
import { createCommands } from '../commands/createCommands';
import { useShortcuts } from '../commands/shortcuts';
import { useExitGuard } from './session/useExitGuard';
import { Workbench } from '../workbench/Workbench';

const registry = createCommands();

export function App() {
  useShortcuts(registry);
  useExitGuard();
  return <CommandProvider registry={registry}><Workbench /></CommandProvider>;
}
