import { describe, expect, it, vi } from 'vitest';
import { installShortcuts } from './shortcuts';
import { createCommands } from './createCommands';
import { useCombatStore } from '../stores/combatStore';
import { useSessionStore, resolveConfirmation } from '../stores/sessionStore';
import { addCharacter, emptyEncounter } from '../characters/rules';
import { player } from '../test/fixtures';

function key(value: string, modifiers: KeyboardEventInit = {}) {
  const event = new KeyboardEvent('keydown', { key: value, ctrlKey: true, cancelable: true, bubbles: true, ...modifiers });
  window.dispatchEvent(event);
  return event.defaultPrevented;
}

describe('character shortcuts', () => {
  it('copies, pastes, quickly deletes on Windows and does not intercept when unavailable', async () => {
    vi.spyOn(navigator, 'platform', 'get').mockReturnValue('Win32');
    const registry = createCommands(), stop = installShortcuts(registry);
    try {
      expect(key('c')).toBe(false);
      useCombatStore.setState({ encounter: addCharacter(emptyEncounter(), player, 'a') });
      await registry.execute('character.select', 'a');
      expect(key('c')).toBe(true);
      expect(key('v')).toBe(true);
      expect(useCombatStore.getState().encounter.combatants).toHaveLength(2);
      expect(key('Delete')).toBe(true);
      expect(useCombatStore.getState().encounter.combatants).toHaveLength(1);
      expect(useSessionStore.getState().selectedId).toBe('a');
    } finally { stop(); }
  });
  it('supports macOS command-backspace and suppresses workspace shortcuts in dialogs', async () => {
    vi.spyOn(navigator, 'platform', 'get').mockReturnValue('MacIntel');
    const registry = createCommands(), stop = installShortcuts(registry);
    try {
      useCombatStore.setState({ encounter: addCharacter(emptyEncounter(), player, 'a') });
      await registry.execute('character.select', 'a');
      const pending = registry.execute('character.remove');
      expect(key('Backspace', { metaKey: true, ctrlKey: false })).toBe(false);
      expect(useCombatStore.getState().encounter.combatants).toHaveLength(1);
      resolveConfirmation(false); await pending;
      useSessionStore.setState({ pickerOpen: true });
      expect(key('i', { shiftKey: true, metaKey: true, ctrlKey: false })).toBe(false);
      useSessionStore.setState({ pickerOpen: false });
      expect(key('Backspace', { metaKey: true, ctrlKey: false })).toBe(true);
      expect(useCombatStore.getState().encounter).toEqual(emptyEncounter());
    } finally { stop(); }
  });
});
