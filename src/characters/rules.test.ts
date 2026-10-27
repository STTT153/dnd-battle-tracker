import { describe, expect, it } from 'vitest';
import { addCharacter, editCharacter, emptyEncounter, removeCharacter } from './rules';
import type { CharacterInput } from './models';

import { player } from '../test/fixtures';

describe('character rules', () => {
  it('keeps inputs immutable, accepts negative initiative and assigns explicit independent IDs', () => {
    const empty = emptyEncounter();
    const next = addCharacter(empty, player, 'p1');
    expect(empty.combatants).toEqual([]);
    expect(next.combatants[0]).toMatchObject({ id: 'p1', initiative: -2, monsterNumber: null });
    expect(() => addCharacter(next, player, 'p1')).toThrow('ID');
  });
  it('validates before changing data', () => {
    const empty = emptyEncounter();
    for (const patch of [{ name: ' ' }, { maxHp: 0 }, { hp: -1 }, { hp: 21 }, { initiative: 0.5 }, { hp: NaN }, { maxHp: Infinity }]) {
      expect(() => addCharacter(empty, { ...player, ...patch }, 'p1')).toThrow();
      expect(empty).toEqual(emptyEncounter());
    }
  });
  it('numbers monsters by existing maximum and preserves numbers on edit', () => {
    const monster: CharacterInput = { ...player, name: '哥布林', kind: 'monster' };
    let battle = addCharacter(addCharacter(emptyEncounter(), monster, 'g1'), monster, 'g2');
    battle = removeCharacter(battle, 'g1');
    battle = addCharacter(battle, monster, 'g3');
    expect(battle.combatants.map((actor) => actor.monsterNumber)).toEqual([2, 3]);
    battle = editCharacter(battle, 'g2', { ...monster, hp: 2 });
    expect(battle.combatants[0].monsterNumber).toBe(2);
    battle = editCharacter(battle, 'g3', { ...monster, name: '食人魔' });
    expect(battle.combatants[1].monsterNumber).toBe(1);
    battle = editCharacter(battle, 'g3', monster);
    expect(battle.combatants[1].monsterNumber).toBe(3);
  });
  it('rejects invalid edits without changing the original', () => {
    const battle = addCharacter(emptyEncounter(), player, 'p1');
    const before = structuredClone(battle);
    expect(() => editCharacter(battle, 'p1', { ...player, hp: 21 })).toThrow();
    expect(battle).toEqual(before);
  });
});
