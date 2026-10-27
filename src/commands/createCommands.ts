import { useWorkbenchStore } from '../stores/workbenchStore';
import { useSessionStore } from '../stores/sessionStore';
import { BattleError } from '../characters/rules';
import { CommandRegistry } from './registry';
import { registerCharacterCommands } from './characterCommands';
import { registerCombatCommands } from './combatCommands';

export function createCommands(): CommandRegistry {
  const registry = new CommandRegistry(() => !!useSessionStore.getState().confirmation, (error) => {
    useSessionStore.setState({ message: error instanceof BattleError ? error.message : '操作失败，请重试。' });
    if (!(error instanceof BattleError)) console.error(error);
  });
  registerCharacterCommands(registry);
  registerCombatCommands(registry);
  (['combat', 'characters', 'monsters'] as const).forEach((view, index) => {
    registry.register({ id: `workbench.view.${view}`, title: ['战斗', '角色', '怪物图鉴'][index],
      icon: (['dice', 'characters', 'book'] as const)[index], execute: () => useWorkbenchStore.getState().setView(view) });
  });
  registry.register({ id: 'workbench.toggleInspector', title: '切换参战者档案', icon: 'inspector',
    execute: () => useWorkbenchStore.getState().togglePanel('inspector') });
  return registry;
}
