import type { MonsterDefinition, MonsterStats } from './models';

function record(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}
const text = (value: unknown) => typeof value === 'string' ? value : '';
const strings = (value: unknown) => Array.isArray(value) ? value.filter((entry): entry is string => typeof entry === 'string') : [];
const number = (value: unknown) => typeof value === 'number' && Number.isSafeInteger(value) ? value : null;

export function adaptHandbook(payload: unknown): MonsterDefinition[] {
  const data = record(payload);
  if (data.schema_version !== 1 || !Array.isArray(data.monsters) || data.monsters.length === 0) {
    throw new Error('图鉴格式无效或没有怪物。');
  }
  const ids = new Set<string>();
  return data.monsters.map((raw) => {
    const entry = record(raw);
    const id = text(entry.id);
    const name = text(entry.name).trim();
    if (!id || !name || ids.has(id)) throw new Error('图鉴包含无效或重复的怪物。');
    ids.add(id);
    const abilities: MonsterStats['abilities'] = {};
    const source = record(entry.abilities);
    for (const key of ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'] as const) {
      const value = record(source[key]);
      const score = number(value.score), modifier = number(value.modifier), savingThrow = number(value.saving_throw);
      if (score !== null && modifier !== null && savingThrow !== null) abilities[key] = { score, modifier, savingThrow };
    }
    const stats: MonsterStats = {
      englishName: text(entry.english_name), classification: text(entry.classification_raw),
      armorClass: text(record(entry.armor_class).raw), speed: text(record(entry.speed).raw), abilities,
      skills: (Array.isArray(entry.skills) ? entry.skills : []).flatMap((rawSkill) => {
        const skill = record(rawSkill), bonus = number(skill.bonus);
        return text(skill.name) && bonus !== null ? [{ name: text(skill.name), bonus }] : [];
      }),
      vulnerabilities: strings(entry.damage_vulnerabilities), resistances: strings(entry.damage_resistances),
      damageImmunities: strings(entry.damage_immunities), conditionImmunities: strings(entry.condition_immunities),
      defenses: text(entry.stat_block_text).split(/\r?\n/).filter((line) => /^(易伤|抗性|免疫)/.test(line)),
      senses: text(entry.senses), languages: strings(entry.languages), challengeRating: text(entry.challenge_rating),
      experiencePoints: number(entry.experience_points), proficiencyBonus: number(entry.proficiency_bonus),
      traits: (Array.isArray(entry.sections) ? entry.sections : []).flatMap((rawSection) => {
        const section = record(rawSection);
        return section.key === 'traits' && text(section.content) ? [text(section.content)] : [];
      }),
    };
    const hp = number(record(entry.hit_points).average);
    return { id, name, englishName: stats.englishName, maxHp: hp !== null && hp >= 1 ? hp : null,
      challengeRating: stats.challengeRating, creatureType: text(entry.creature_type), stats };
  });
}

export async function loadHandbook() {
  const { default: source } = await import('../../resources/monster_handbook.JSON?raw');
  return adaptHandbook(JSON.parse(source));
}

export function searchMonsters(monsters: MonsterDefinition[], query: string) {
  const term = query.trim().toLowerCase();
  return monsters.filter((monster) => monster.name.toLowerCase().includes(term) || monster.englishName.toLowerCase().includes(term));
}
