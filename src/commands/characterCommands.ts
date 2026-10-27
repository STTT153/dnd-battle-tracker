import { prepareCharacter, selectCharacter, submitCharacter, removeSelected, chooseMonster } from '../characters/characterActions';
import { addCharacter, displayName, getActor } from '../characters/rules';
import { useCombatStore } from '../stores/combatStore';
import { askConfirmation, useSessionStore } from '../stores/sessionStore';
import { ensureHandbook, recordRecent } from '../stores/handbookStore';
import type { CommandRegistry } from './registry';

export function registerCharacterCommands(registry: CommandRegistry) {
  const selection = () => ({ enabled: !!useSessionStore.getState().selectedId, reason: '请先选择一名参战者。' });
  registry.register({ id: 'character.addPlayer', title: '添加玩家', icon: 'addPlayer', execute: () => prepareCharacter('player') });
  registry.register({ id: 'character.addNpc', title: '添加 NPC', icon: 'characters', execute: () => prepareCharacter('npc') });
  registry.register({ id: 'character.addMonster', title: '添加怪物', icon: 'monster', execute: () => {
    useSessionStore.setState({ pickerOpen: true });
    void ensureHandbook();
  } });
  registry.register({ id: 'character.addManualMonster', title: '手动添加怪物', icon: 'monster', execute: () => {
    useSessionStore.setState({ pickerOpen: false });
    prepareCharacter('monster');
  } });
  registry.register({ id: 'character.select', title: '选择参战者', icon: 'characters', execute: selectCharacter });
  registry.register({ id: 'character.updateDraft', title: '编辑草稿', icon: 'edit', execute: (patch) => {
    useSessionStore.setState((state) => ({ draft: { ...state.draft, ...patch }, formError: '' }));
  } });
  registry.register({ id: 'character.submit', title: '提交角色资料', icon: 'check', execute: submitCharacter });
  registry.register({ id: 'character.filter', title: '筛选角色类型', icon: 'filter', execute: (filter) => { useSessionStore.setState({ filter }); } });
  registry.register({ id: 'character.copy', title: '复制角色', icon: 'copy', availability: selection, execute: () => {
    const { id: _id, monsterNumber: _number, ...input } = getActor(useCombatStore.getState().encounter, useSessionStore.getState().selectedId);
    useSessionStore.setState({ copied: structuredClone(input), message: '已复制角色，可粘贴为新参战者。' });
  } });
  registry.register({ id: 'character.paste', title: '粘贴角色', icon: 'paste',
    availability: () => ({ enabled: !!useSessionStore.getState().copied, reason: '请先复制一名角色。' }), execute: () => {
      const input = useSessionStore.getState().copied!;
      const id = crypto.randomUUID();
      useCombatStore.setState((state) => ({ encounter: addCharacter(state.encounter, input, id) }));
      selectCharacter(id);
    } });
  registry.register({ id: 'character.remove', title: '移除所选', icon: 'trash', availability: selection, execute: async () => {
    const id = useSessionStore.getState().selectedId!;
    const actor = getActor(useCombatStore.getState().encounter, id);
    if (!await askConfirmation('移除参战者', `确定移除“${displayName(actor)}”？此操作不会增加轮数。`, '移除')) return false;
    removeSelected(id);
  } });
  registry.register({ id: 'character.quickRemove', title: '快速删除所选', icon: 'trash', availability: selection,
    execute: () => removeSelected(useSessionStore.getState().selectedId!) });
  registry.register({ id: 'monster.choose', title: '选用怪物', icon: 'check', execute: (monster) => {
    chooseMonster(monster); recordRecent(monster);
  } });
  registry.register({ id: 'monster.closePicker', title: '关闭怪物选择', icon: 'close', execute: () => { useSessionStore.setState({ pickerOpen: false }); } });
  registry.register({ id: 'monster.retry', title: '重试加载图鉴', icon: 'reset', execute: () => ensureHandbook(true) });
}
