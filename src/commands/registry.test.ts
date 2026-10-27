import { describe, expect, it, vi } from 'vitest';
import { CommandRegistry, type Command } from './registry';
import { createCommands } from './createCommands';
import { useCombatStore } from '../stores/combatStore';

describe('Command Registry', () => {
  it('guards disabled commands even when invoked outside the UI', async () => {
    const registry = new CommandRegistry();
    const execute = vi.fn();
    let enabled = false;
    registry.register({ id: 'combat.start', title: '开始', icon: 'play', execute,
      availability: () => ({ enabled, reason: '暂不可用' }) });
    expect(await registry.execute('combat.start')).toBe(false);
    expect(execute).not.toHaveBeenCalled();
    enabled = true;
    expect(await registry.execute('combat.start')).toBe(true);
    expect(execute).toHaveBeenCalledOnce();
  });

  it('rejects duplicates and safely unregisters extensions', async () => {
    const registry = new CommandRegistry();
    const command: Command<'combat.start'> = { id: 'combat.start', title: '开始', icon: 'play', execute: vi.fn() };
    const unregister = registry.register(command);
    expect(() => registry.register(command)).toThrow('命令已注册');
    unregister();
    await expect(registry.execute(command.id)).rejects.toThrow('命令未注册');
    const replacement = { ...command, execute: vi.fn() };
    registry.register(replacement);
    unregister();
    await registry.execute(command.id);
    expect(replacement.execute).toHaveBeenCalledOnce();
  });

  it('guards empty combat operations without mutating combat', async () => {
    const registry = createCommands();
    const before = structuredClone(useCombatStore.getState().encounter);
    for (const id of ['combat.start', 'combat.nextTurn', 'combat.stop', 'combat.reset'] as const) {
      expect(registry.getAvailability(id).enabled).toBe(false);
      expect(await registry.execute(id)).toBe(false);
    }
    expect(useCombatStore.getState().encounter).toEqual(before);
  });
});
