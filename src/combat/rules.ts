import type { Encounter } from '../types/encounter';
import { BattleError, getActor, integer } from '../characters/rules';

export function sortEncounter(encounter: Encounter): Encounter {
  return { ...encounter, combatants: [...encounter.combatants].sort((a, b) => b.initiative - a.initiative) };
}

export function moveTied(encounter: Encounter, id: string, direction: -1 | 1): Encounter {
  getActor(encounter, id);
  if (direction !== -1 && direction !== 1) throw new BattleError('移动方向无效。');
  const index = encounter.combatants.findIndex((actor) => actor.id === id), target = index + direction;
  if (target < 0 || target >= encounter.combatants.length) throw new BattleError('已到列表边界，无法继续移动。');
  if (encounter.combatants[index].initiative !== encounter.combatants[target].initiative) {
    throw new BattleError('只能与相邻且先攻相同的角色交换顺序；请先点击排序。');
  }
  const combatants = [...encounter.combatants];
  [combatants[index], combatants[target]] = [combatants[target], combatants[index]];
  return { ...encounter, combatants };
}

export function startCombat(encounter: Encounter): Encounter {
  if (!encounter.combatants.length) throw new BattleError('战斗列表为空，请先添加参战者。');
  if (encounter.active) throw new BattleError('战斗已经开始，请使用“下一位”。');
  const sorted = sortEncounter(encounter);
  return { ...sorted, active: true, round: 1, currentId: sorted.combatants[0].id, actedIds: [] };
}

export function stopCombat(encounter: Encounter): Encounter {
  if (!encounter.active) throw new BattleError('当前没有进行中的战斗。');
  return { ...encounter, active: false, round: 0, currentId: null, actedIds: [] };
}

export function nextTurn(encounter: Encounter): Encounter {
  if (!encounter.combatants.length) throw new BattleError('战斗列表为空，请先添加参战者。');
  if (!encounter.active) throw new BattleError('请先点击“开始战斗”。');
  const actedIds = encounter.currentId === null ? [...encounter.actedIds] : [...encounter.actedIds, encounter.currentId];
  const pending = encounter.combatants.find((actor) => !actedIds.includes(actor.id));
  return pending ? { ...encounter, actedIds, currentId: pending.id }
    : { ...encounter, round: encounter.round + 1, currentId: encounter.combatants[0].id, actedIds: [] };
}

export function changeHp(encounter: Encounter, id: string, action: 'damage' | 'heal' | 'correct', amount: number): Encounter {
  const actor = getActor(encounter, id);
  integer(amount, action === 'correct' ? '当前生命值' : '血量操作数值', 0);
  if (action === 'correct' && amount > actor.maxHp) throw new BattleError('当前生命值不能超过最大生命值。');
  const hp = action === 'correct' ? amount : action === 'damage' ? Math.max(0, actor.hp - amount) : Math.min(actor.maxHp, actor.hp + amount);
  return { ...encounter, combatants: encounter.combatants.map((entry) => entry.id === id ? { ...entry, hp } : entry) };
}
