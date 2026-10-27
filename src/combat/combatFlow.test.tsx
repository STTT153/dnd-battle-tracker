import { describe, expect, it } from 'vitest';
import { act, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../app/App';
import { createCommands } from '../commands/createCommands';
import { useCombatStore } from '../stores/combatStore';
import { useSessionStore } from '../stores/sessionStore';
import { addCharacter, emptyEncounter } from '../characters/rules';
import { player } from '../test/fixtures';

function addParty() {
  let encounter = emptyEncounter();
  for (const [id, initiative] of [['a', 20], ['b', 10]] as const) encounter = addCharacter(encounter, { ...player, name: id, initiative }, id);
  useCombatStore.setState({ encounter });
}

describe('combat UI and command integration', () => {
  it('reactively enables start, separates selection from actor and operates HP', async () => {
    const registry = createCommands(), user = userEvent.setup();
    render(<App />);
    const toolbar = within(screen.getByRole('toolbar'));
    expect(toolbar.getByRole('button', { name: '开始战斗' })).toBeDisabled();
    act(addParty);
    expect(toolbar.getByRole('button', { name: '开始战斗' })).toBeEnabled();
    await user.click(toolbar.getByRole('button', { name: '开始战斗' }));
    expect(useCombatStore.getState().encounter).toMatchObject({ active: true, round: 1, currentId: 'a' });
    expect(toolbar.getByRole('button', { name: '开始战斗' })).toBeDisabled();
    expect(await registry.execute('combat.start')).toBe(false);
    await user.click(within(screen.getByRole('table')).getByRole('button', { name: 'b' }));
    expect(useSessionStore.getState().selectedId).toBe('b');
    expect(useCombatStore.getState().encounter.currentId).toBe('a');
    await user.clear(screen.getByRole('textbox', { name: '血量操作数值' }));
    await user.type(screen.getByRole('textbox', { name: '血量操作数值' }), '99');
    await user.click(screen.getByRole('button', { name: '受到伤害' }));
    expect(useCombatStore.getState().encounter.combatants[1].hp).toBe(0);
    await user.click(toolbar.getByRole('button', { name: '下一位' }));
    expect(useCombatStore.getState().encounter.currentId).toBe('b');
    expect(useSessionStore.getState().selectedId).toBe('b');
    expect(screen.getByLabelText('当前 HP')).toHaveValue('0');
    await user.click(screen.getByRole('button', { name: '接受治疗' }));
    expect(useCombatStore.getState().encounter.combatants[1].hp).toBe(20);
    await user.click(toolbar.getByRole('button', { name: '结束战斗' }));
    expect(useCombatStore.getState().encounter).toMatchObject({ active: false, round: 0, currentId: null });
    expect(useCombatStore.getState().encounter.combatants).toHaveLength(2);
  });
  it('cancels and confirms reset while blocking unrelated commands during confirmation', async () => {
    addParty();
    const registry = createCommands(), user = userEvent.setup();
    render(<App />);
    let pending: Promise<boolean>;
    act(() => { pending = registry.execute('combat.reset'); });
    const dialog = within(screen.getByRole('dialog', { name: '清空战斗' }));
    expect(await registry.execute('character.addPlayer')).toBe(false);
    await user.click(dialog.getByRole('button', { name: '取消' }));
    expect(await pending!).toBe(false);
    expect(useCombatStore.getState().encounter.combatants).toHaveLength(2);
    act(() => { pending = registry.execute('combat.reset'); });
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: '清空' }));
    expect(await pending!).toBe(true);
    expect(useCombatStore.getState().encounter).toEqual(emptyEncounter());
    expect(useSessionStore.getState().selectedId).toBeNull();
  });
  it('deletes the selected next/previous actor and pastes independent copied data', async () => {
    addParty(); const registry = createCommands();
    await registry.execute('character.select', 'a');
    await registry.execute('character.copy');
    await registry.execute('character.quickRemove');
    expect(useSessionStore.getState().selectedId).toBe('b');
    await registry.execute('character.paste');
    const pasted = useCombatStore.getState().encounter.combatants[1];
    await registry.execute('character.quickRemove');
    expect(useSessionStore.getState().selectedId).toBe('b');
    expect(pasted.id).not.toBe('a');
  });
});
