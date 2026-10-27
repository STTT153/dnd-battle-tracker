import type { CharacterInput } from './models';
import type { Combatant, Encounter } from '../types/encounter';

export class BattleError extends Error {}

export function integer(value: number, label: string, minimum?: number) {
  if (!Number.isSafeInteger(value)) throw new BattleError(`${label}必须是安全范围内的整数。`);
  if (minimum !== undefined && value < minimum) throw new BattleError(`${label}不能小于 ${minimum}。`);
  return value;
}

export function validateCharacter(input: CharacterInput) {
  if (!input.name.trim()) throw new BattleError('请输入参战者名称。');
  if (!['player', 'npc', 'monster'].includes(input.kind)) throw new BattleError('类型必须是玩家、NPC 或怪物。');
  integer(input.initiative, '先攻值');
  integer(input.maxHp, '最大生命值', 1);
  integer(input.hp, '当前生命值', 0);
  if (input.hp > input.maxHp) throw new BattleError('当前生命值不能超过最大生命值。');
}

export function displayName(actor: Combatant) {
  return actor.kind === 'monster' ? `${actor.name} ${actor.monsterNumber}` : actor.name;
}

export function getActor(encounter: Encounter, id: string | null) {
  const actor = encounter.combatants.find((entry) => entry.id === id);
  if (!actor) throw new BattleError('请先在列表中选择一名参战者。');
  return actor;
}

function nextNumber(encounter: Encounter, name: string, excludedId?: string) {
  return Math.max(0, ...encounter.combatants.filter((actor) => actor.kind === 'monster'
    && actor.name === name && actor.id !== excludedId).map((actor) => actor.monsterNumber ?? 0)) + 1;
}

export function addCharacter(encounter: Encounter, input: CharacterInput, id: string): Encounter {
  validateCharacter(input);
  if (!id || encounter.combatants.some((actor) => actor.id === id)) throw new BattleError('角色 ID 为空或重复。');
  const name = input.name.trim();
  const actor: Combatant = {
    ...structuredClone(input), id, name,
    monsterNumber: input.kind === 'monster' ? nextNumber(encounter, name) : null,
    monsterDefinitionId: input.kind === 'monster' ? input.monsterDefinitionId : undefined,
    monsterStats: input.kind === 'monster' ? structuredClone(input.monsterStats) : null,
  };
  const combatants = [...encounter.combatants, actor];
  return { ...encounter, combatants, currentId: encounter.active && encounter.currentId === null
    ? combatants.find((entry) => !encounter.actedIds.includes(entry.id))?.id ?? null : encounter.currentId };
}

export function editCharacter(encounter: Encounter, id: string, input: CharacterInput): Encounter {
  const old = getActor(encounter, id);
  validateCharacter(input);
  const name = input.name.trim();
  const actor: Combatant = { ...old, ...structuredClone(input), name,
    monsterNumber: input.kind === 'monster'
      ? old.kind === 'monster' && old.name === name ? old.monsterNumber : nextNumber(encounter, name, id)
      : null,
    monsterDefinitionId: input.kind === 'monster' ? input.monsterDefinitionId : undefined,
    monsterStats: input.kind === 'monster' ? structuredClone(input.monsterStats) : null,
  };
  return { ...encounter, combatants: encounter.combatants.map((entry) => entry.id === id ? actor : entry) };
}

export function emptyEncounter(): Encounter {
  return { combatants: [], active: false, round: 0, currentId: null, actedIds: [] };
}

export function removeCharacter(encounter: Encounter, id: string): Encounter {
  getActor(encounter, id);
  const combatants = encounter.combatants.filter((actor) => actor.id !== id);
  if (!combatants.length) return emptyEncounter();
  const actedIds = encounter.actedIds.filter((actedId) => actedId !== id);
  return { ...encounter, combatants, actedIds,
    currentId: encounter.currentId === id
      ? combatants.find((actor) => !actedIds.includes(actor.id))?.id ?? null : encounter.currentId };
}
