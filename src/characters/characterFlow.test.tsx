import { describe, expect, it } from 'vitest';
import { act, fireEvent, render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../app/App';
import { useCombatStore } from '../stores/combatStore';
import { useSessionStore } from '../stores/sessionStore';
import { useHandbookStore } from '../stores/handbookStore';
import { createCommands } from '../commands/createCommands';
import { loadHandbook } from './handbook';

describe('character workflow', () => {
  it('adds, validates, edits, copies and removes through commands and UI', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(within(screen.getByRole('toolbar')).getByRole('button', { name: '添加玩家' }));
    const inspector = within(screen.getByRole('complementary', { name: '参战者档案' }));
    await user.type(inspector.getByLabelText('名称'), '法师');
    await user.clear(inspector.getByLabelText('最大 HP'));
    await user.type(inspector.getByLabelText('最大 HP'), '0');
    await user.click(inspector.getByRole('button', { name: '确认添加' }));
    expect(screen.getByRole('alert')).toHaveTextContent('最大生命值不能小于 1');
    expect(useCombatStore.getState().encounter.combatants).toHaveLength(0);
    await user.clear(inspector.getByLabelText('最大 HP'));
    await user.type(inspector.getByLabelText('最大 HP'), '20');
    await user.click(inspector.getByRole('button', { name: '确认添加' }));
    const actor = useCombatStore.getState().encounter.combatants[0];
    expect(actor.hp).toBe(20);
    await user.clear(inspector.getByLabelText('当前 HP'));
    await user.type(inspector.getByLabelText('当前 HP'), '3');
    await user.click(inspector.getByRole('button', { name: '保存修改' }));
    expect(useCombatStore.getState().encounter.combatants[0].hp).toBe(3);
    const registry = createCommands();
    await act(async () => { await registry.execute('character.copy'); await registry.execute('character.paste'); });
    expect(useCombatStore.getState().encounter.combatants).toHaveLength(2);
    const copy = useCombatStore.getState().encounter.combatants[1];
    expect(copy.id).not.toBe(actor.id);
    expect(copy.hp).toBe(3);
    // The ordinary remove path must wait for confirmation.
    let removing: Promise<boolean>;
    act(() => { removing = registry.execute('character.remove'); });
    await waitFor(() => expect(screen.getByRole('dialog', { name: '移除参战者' })).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: '取消' }));
    expect(await removing!).toBe(false);
    expect(useCombatStore.getState().encounter.combatants).toHaveLength(2);
    await act(async () => { await registry.execute('character.quickRemove'); });
    expect(useSessionStore.getState().selectedId).toBe(actor.id);
  });

  it('allows manual monsters when the handbook fails and preserves hidden drafts', async () => {
    useHandbookStore.setState({ status: 'error', error: '图鉴不可用' });
    const user = userEvent.setup();
    render(<App />);
    await user.click(within(screen.getByRole('toolbar')).getByRole('button', { name: '添加怪物' }));
    expect(screen.getByRole('alert')).toHaveTextContent('图鉴不可用');
    await user.click(screen.getByRole('button', { name: '手动添加怪物' }));
    await user.type(screen.getByLabelText('名称'), '哥布林');
    await user.click(screen.getByRole('button', { name: '关闭参战者档案' }));
    await user.click(screen.getByRole('button', { name: '切换参战者档案' }));
    expect(screen.getByLabelText('名称')).toHaveValue('哥布林');
    fireEvent.submit(screen.getByRole('form', { name: '新增参战者' }));
    expect(useCombatStore.getState().encounter.combatants[0]).toMatchObject({ kind: 'monster', name: '哥布林', monsterNumber: 1 });
  });
  it('selects a handbook monster by English search and Enter, then commits a numbered instance', async () => {
    const monsters = await loadHandbook();
    useHandbookStore.setState({ monsters, status: 'ready' });
    const user = userEvent.setup();
    render(<App />);
    await user.click(within(screen.getByRole('toolbar')).getByRole('button', { name: '添加怪物' }));
    const picker = within(screen.getByRole('dialog', { name: '选择怪物' }));
    await user.type(picker.getByRole('searchbox'), 'Grell');
    expect(picker.getAllByRole('option')).toHaveLength(1);
    await user.keyboard('{Enter}');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    const inspector = within(screen.getByRole('complementary', { name: '参战者档案' }));
    expect(inspector.getByLabelText('名称')).toHaveValue('触须怪');
    expect(inspector.getByLabelText('先攻值')).toHaveValue('0');
    expect(inspector.getByLabelText('最大 HP')).toHaveValue('55');
    expect(inspector.getByLabelText('当前 HP')).toHaveValue('');
    expect(inspector.getByText('免疫闪电、倒地')).toBeInTheDocument();
    await user.click(inspector.getByRole('button', { name: '确认添加' }));
    expect(useCombatStore.getState().encounter.combatants[0]).toMatchObject({ name: '触须怪', hp: 55, monsterNumber: 1 });
    expect(useHandbookStore.getState().recent[0].englishName).toBe('Grell');
  });

  it('filters the shared encounter and removes to the next visible participant', async () => {
    const registry = createCommands();
    for (const [kind, name] of [['player', '战士'], ['npc', '向导'], ['player', '法师']] as const) {
      await registry.execute(kind === 'npc' ? 'character.addNpc' : 'character.addPlayer');
      await registry.execute('character.updateDraft', { name });
      await registry.execute('character.submit');
    }
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('button', { name: '角色' }));
    await user.selectOptions(screen.getByRole('combobox', { name: '类型' }), 'player');
    const table = within(screen.getByRole('table'));
    expect(table.queryByRole('button', { name: '向导' })).not.toBeInTheDocument();
    await user.click(table.getByRole('button', { name: '战士' }));
    await act(async () => { await registry.execute('character.quickRemove'); });
    const selected = useCombatStore.getState().encounter.combatants.find((actor) => actor.id === useSessionStore.getState().selectedId);
    expect(selected?.name).toBe('法师');
    expect(useCombatStore.getState().encounter.combatants.map((actor) => actor.name)).toEqual(['向导', '法师']);
  });

});
