import { create } from 'zustand';
import type { Encounter } from '../types/encounter';
import { emptyEncounter } from '../characters/rules';

export const useCombatStore = create<{ encounter: Encounter }>(() => ({
  encounter: emptyEncounter(),
}));
