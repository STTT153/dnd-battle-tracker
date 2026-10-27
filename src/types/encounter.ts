import type { Character, MonsterDefinition, MonsterStats } from '../characters/models';

export interface Combatant extends Character {
  hp: number;
  monsterNumber: number | null;
  monsterDefinitionId?: MonsterDefinition['id'];
  monsterStats: MonsterStats | null;
}

/** Internal model; legacy JSON conversion belongs to the later storage phase. */
export interface Encounter {
  combatants: Combatant[];
  active: boolean;
  round: number;
  currentId: string | null;
  actedIds: string[];
}
