import { IconButton } from '../components/IconButton';
import { useCommands } from './CommandProvider';
import type { SimpleCommandId } from './registry';
import { useCombatStore } from '../stores/combatStore';
import { useSessionStore } from '../stores/sessionStore';

export function CommandButton({ id, pressed, className, text = false }: {
  id: SimpleCommandId; pressed?: boolean; className?: string; text?: boolean;
}) {
  useCombatStore();
  useSessionStore();
  const registry = useCommands();
  const command = registry.get(id);
  const availability = registry.getAvailability(id);
  return <IconButton icon={command.icon} label={command.title} pressed={pressed}
    disabled={!availability.enabled} disabledReason={availability.reason}
    className={className} onClick={() => { void registry.execute(id); }}>
    {text ? command.title : undefined}
  </IconButton>;
}
