export type CharacterKind = 'player' | 'npc' | 'monster';

export const kindLabels: Record<CharacterKind, string> = { player: '玩家', npc: 'NPC', monster: '怪物' };

export interface MonsterStats {
  englishName: string;
  classification: string;
  armorClass: string;
  speed: string;
  abilities: Partial<Record<'strength' | 'dexterity' | 'constitution' | 'intelligence' | 'wisdom' | 'charisma', {
    score: number; modifier: number; savingThrow: number;
  }>>;
  skills: { name: string; bonus: number }[];
  vulnerabilities: string[];
  resistances: string[];
  damageImmunities: string[];
  conditionImmunities: string[];
  defenses: string[];
  senses: string;
  languages: string[];
  challengeRating: string;
  experiencePoints: number | null;
  proficiencyBonus: number | null;
  traits: string[];
}

export interface Character {
  id: string;
  name: string;
  kind: CharacterKind;
  initiative: number;
  maxHp: number;
}

/** A handbook template, never a mutable combat instance. */
export interface MonsterDefinition {
  id: string;
  name: string;
  englishName: string;
  maxHp: number | null;
  challengeRating: string;
  creatureType: string;
  stats: MonsterStats;
}

export interface CharacterInput {
  name: string;
  kind: CharacterKind;
  initiative: number;
  maxHp: number;
  hp: number;
  monsterDefinitionId?: string;
  monsterStats: MonsterStats | null;
}
