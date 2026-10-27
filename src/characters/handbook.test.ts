import { describe, expect, it } from 'vitest';
import { adaptHandbook, loadHandbook, searchMonsters } from './handbook';
import { ensureHandbook, recordRecent, useHandbookStore } from '../stores/handbookStore';
import { addCharacter, emptyEncounter } from './rules';
import { player } from '../test/fixtures';

describe('local handbook', () => {
  it('adapts all 503 entries and preserves Grell defenses and traits without actions or HP copies', async () => {
    const monsters = await loadHandbook();
    expect(monsters).toHaveLength(503);
    const grell = monsters.find((monster) => monster.englishName === 'Grell')!;
    expect(grell.stats.armorClass).toBe('12');
    expect(grell.stats.abilities.strength?.savingThrow).toBe(2);
    expect(grell.stats.defenses).toContain('免疫闪电、倒地');
    expect(grell.stats.traits[0]).toContain('劫持Abduct');
    expect(grell.stats).not.toHaveProperty('actions');
    expect(grell.stats).not.toHaveProperty('hit_points');
    expect(searchMonsters(monsters, ' GRELL ')).toContain(grell);
    expect(searchMonsters(monsters, '触须怪')).toContain(grell);
    expect(searchMonsters(monsters, '不存在的怪物123')).toEqual([]);
    const battle = addCharacter(emptyEncounter(), { ...player, kind: 'monster', monsterStats: grell.stats }, 'g1');
    battle.combatants[0].monsterStats!.traits.push('新特质');
    expect(grell.stats.traits).not.toContain('新特质');
  });
  it('keeps six deduplicated recent choices', async () => {
    const monsters = await loadHandbook();
    monsters.slice(0, 8).forEach(recordRecent);
    recordRecent(monsters[3]);
    const recent = useHandbookStore.getState().recent;
    expect(recent).toHaveLength(6);
    expect(recent[0].id).toBe(monsters[3].id);
    expect(new Set(recent.map((monster) => monster.id)).size).toBe(6);
  });
  it('reports malformed data, permits retry and recovers', async () => {
    expect(() => adaptHandbook({ schema_version: 99, monsters: [] })).toThrow();
    await ensureHandbook(false, async () => { throw new Error('测试损坏'); });
    expect(useHandbookStore.getState()).toMatchObject({ status: 'error', error: expect.stringContaining('测试损坏') });
    await ensureHandbook(true);
    expect(useHandbookStore.getState().status).toBe('ready');
  });
});
