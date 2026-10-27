import { useCombatStore } from '../stores/combatStore';
import { askConfirmation, newDraft, useSessionStore } from '../stores/sessionStore';
import { selectCharacter } from '../characters/characterActions';
import { BattleError, emptyEncounter } from '../characters/rules';
import { changeHp, moveTied, nextTurn, sortEncounter, startCombat, stopCombat } from '../combat/rules';
import type { Encounter } from '../types/encounter';
import type { CommandRegistry } from './registry';

function apply(encounter: Encounter, followCurrent = false) {
  useCombatStore.setState({ encounter });
  useSessionStore.setState({ message: '' });
  const id = followCurrent ? encounter.currentId : useSessionStore.getState().selectedId;
  if (id && encounter.combatants.some((actor) => actor.id === id)) selectCharacter(id);
}

export function registerCombatCommands(registry: CommandRegistry) {
  const battle = () => useCombatStore.getState().encounter;
  const active = () => ({ enabled: battle().active, reason: '请先开始战斗。' });
  const selected = () => ({ enabled: !!useSessionStore.getState().selectedId, reason: '请先选择一名参战者。' });
  registry.register({ id: 'combat.start', title: '开始战斗', icon: 'play',
    availability: () => ({ enabled: !battle().active && battle().combatants.length > 0, reason: battle().active ? '战斗已开始。' : '请先添加参战者。' }),
    execute: () => apply(startCombat(battle()), true) });
  registry.register({ id: 'combat.nextTurn', title: '下一位', icon: 'next', availability: active,
    execute: () => apply(nextTurn(battle()), true) });
  registry.register({ id: 'combat.stop', title: '结束战斗', icon: 'stop', availability: active,
    execute: () => {
      apply(stopCombat(battle()));
      useSessionStore.setState({ message: '战斗已结束；参战者、顺序与当前 HP 已保留。' });
    } });
  registry.register({ id: 'combat.reset', title: '清空战斗', icon: 'reset',
    availability: () => ({ enabled: battle().combatants.length > 0, reason: '战斗已经为空。' }),
    execute: async () => {
      if (!await askConfirmation('清空战斗', '确定清空所有参战者和轮次？本次内存战斗无法恢复。', '清空')) return false;
      useCombatStore.setState({ encounter: emptyEncounter() });
      useSessionStore.setState({ selectedId: null, editId: null, draft: newDraft(), formError: '', message: '已清空战斗。' });
    } });
  registry.register({ id: 'combat.sort', title: '按先攻排序', icon: 'sort',
    availability: () => ({ enabled: battle().combatants.length > 1, reason: '至少需要两名参战者。' }),
    execute: () => apply(sortEncounter(battle())) });
  for (const [id, title, icon, direction] of [
    ['combat.moveUp', '同先攻上移', 'up', -1], ['combat.moveDown', '同先攻下移', 'down', 1],
  ] as const) registry.register({ id, title, icon, availability: () => {
    const encounter = battle(), selectedId = useSessionStore.getState().selectedId;
    const index = encounter.combatants.findIndex((actor) => actor.id === selectedId);
    return { enabled: index >= 0 && encounter.combatants[index + direction]?.initiative === encounter.combatants[index].initiative,
      reason: '只能与相邻且先攻相同的角色交换顺序。' };
  }, execute: () => apply(moveTied(battle(), useSessionStore.getState().selectedId!, direction)) });
  registry.register({ id: 'combat.setAmount', title: '填写血量操作数值', icon: 'edit', execute: (hpAmount) => { useSessionStore.setState({ hpAmount }); } });
  for (const action of ['damage', 'heal'] as const) registry.register({ id: `combat.${action}`,
    title: action === 'damage' ? '受到伤害' : '接受治疗', icon: action, availability: selected,
    execute: () => {
      const { hpAmount, selectedId } = useSessionStore.getState();
      if (!/^[+-]?\d+$/.test(hpAmount.trim())) throw new BattleError('血量操作数值请输入整数。');
      apply(changeHp(battle(), selectedId!, action, Number(hpAmount.trim())));
    } });
}
