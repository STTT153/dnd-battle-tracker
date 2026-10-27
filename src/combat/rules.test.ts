import { describe, expect, it } from 'vitest';
import { addCharacter, editCharacter, emptyEncounter, removeCharacter } from '../characters/rules';
import { player } from '../test/fixtures';
import { changeHp, moveTied, nextTurn, sortEncounter, startCombat, stopCombat } from './rules';
import type { Encounter } from '../types/encounter';

function party(): Encounter {
  let battle = emptyEncounter();
  for (const [id, initiative] of [['a', 30], ['b', 20], ['c', 10]] as const) {
    battle = addCharacter(battle, { ...player, name: id, initiative }, id);
  }
  return battle;
}

describe('combat rules', () => {
  it('sorts stably and preserves manually changed tie order', () => {
    let battle = party();
    battle = editCharacter(battle, 'a', { ...player, initiative: 20 });
    battle = sortEncounter(battle);
    expect(battle.combatants.map((actor) => actor.id)).toEqual(['a', 'b', 'c']);
    battle = sortEncounter(moveTied(battle, 'b', -1));
    expect(battle.combatants.map((actor) => actor.id)).toEqual(['b', 'a', 'c']);
    expect(() => moveTied(battle, 'b', -1)).toThrow('边界');
    expect(() => moveTied(battle, 'a', 1)).toThrow('相同');
  });
  it('rejects empty, premature and repeated starts without changing inputs', () => {
    expect(() => startCombat(emptyEncounter())).toThrow('为空');
    expect(() => nextTurn(party())).toThrow('先点击');
    expect(() => stopCombat(party())).toThrow('没有进行');
    const battle = startCombat(party()), before = structuredClone(battle);
    expect(() => startCombat(battle)).toThrow('已经开始');
    expect(battle).toEqual(before);
  });
  it('advances single-actor battles across rounds', () => {
    let battle = startCombat(addCharacter(emptyEncounter(), player, 'a'));
    battle = nextTurn(nextTurn(battle));
    expect(battle).toMatchObject({ round: 3, currentId: 'a', actedIds: [] });
  });
  it('chooses pending actors in display order without losing current actor after sorting', () => {
    let battle = nextTurn(startCombat(party()));
    battle = editCharacter(battle, 'c', { ...player, initiative: 50 });
    battle = sortEncounter(battle);
    expect(battle).toMatchObject({ round: 1, currentId: 'b', actedIds: ['a'] });
    battle = nextTurn(battle);
    expect(battle).toMatchObject({ round: 1, currentId: 'c' });
    expect(nextTurn(battle)).toMatchObject({ round: 2, currentId: 'c', actedIds: [] });
  });
  it('includes newly added high initiative actors in this round', () => {
    let battle = nextTurn(startCombat(party()));
    battle = sortEncounter(addCharacter(battle, { ...player, initiative: 60 }, 'd'));
    expect(battle.currentId).toBe('b');
    battle = nextTurn(battle);
    expect(battle).toMatchObject({ currentId: 'd', round: 1 });
    expect(nextTurn(battle)).toMatchObject({ currentId: 'c', round: 1 });
  });
  it('removes current actor without advancing a round and prunes acted IDs', () => {
    let battle = nextTurn(startCombat(party()));
    battle = removeCharacter(battle, 'b');
    expect(battle).toMatchObject({ currentId: 'c', round: 1, actedIds: ['a'] });
    battle = removeCharacter(battle, 'a');
    expect(battle).toMatchObject({ currentId: 'c', round: 1, actedIds: [] });
    expect(removeCharacter(battle, 'c')).toEqual(emptyEncounter());
  });
  it('defers round increment when the last pending actor is removed', () => {
    let battle = nextTurn(nextTurn(startCombat(party())));
    battle = removeCharacter(battle, 'c');
    expect(battle).toMatchObject({ currentId: null, round: 1, active: true });
    expect(nextTurn(battle)).toMatchObject({ currentId: 'a', round: 2, actedIds: [] });
    const added = addCharacter(battle, player, 'd');
    expect(added).toMatchObject({ currentId: 'd', round: 1 });
  });
  it('removing other actors leaves current actor and round unchanged', () => {
    const battle = nextTurn(startCombat(party()));
    expect(removeCharacter(removeCharacter(battle, 'a'), 'c')).toMatchObject({ currentId: 'b', round: 1 });
  });
  it('clamps damage and healing; rejects invalid direct HP and negative amounts', () => {
    const battle = startCombat(party());
    const damaged = changeHp(battle, 'a', 'damage', 99);
    expect(damaged.combatants[0].hp).toBe(0);
    expect(changeHp(damaged, 'a', 'heal', 99).combatants[0].hp).toBe(20);
    expect(changeHp(damaged, 'a', 'correct', 3).combatants[0].hp).toBe(3);
    for (const amount of [-1, 0.5, NaN, Infinity]) expect(() => changeHp(battle, 'a', 'damage', amount)).toThrow();
    expect(() => changeHp(battle, 'a', 'correct', 21)).toThrow('超过');
    expect(battle.combatants[0].hp).toBe(20);
  });
  it.each(['player', 'npc', 'monster'] as const)('does not skip or end zero HP %s turns', (kind) => {
    let battle = startCombat(addCharacter(emptyEncounter(), { ...player, kind }, 'a'));
    battle = changeHp(battle, 'a', 'damage', 99);
    expect(nextTurn(battle)).toMatchObject({ active: true, currentId: 'a', round: 2 });
  });
  it('stops without restoring HP, deleting actors or changing display order', () => {
    let battle = nextTurn(startCombat(party()));
    battle = changeHp(battle, 'a', 'damage', 8);
    const stopped = stopCombat(battle);
    expect(stopped.combatants).toEqual(battle.combatants);
    expect(stopped).toMatchObject({ active: false, round: 0, currentId: null, actedIds: [] });
    expect(startCombat(stopped)).toMatchObject({ round: 1, currentId: 'a' });
    expect(startCombat(stopped).combatants[0].hp).toBe(12);
  });
});
