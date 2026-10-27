import { create } from 'zustand';
import type { CharacterInput, CharacterKind, MonsterStats } from '../characters/models';

export interface CharacterDraft {
  name: string;
  kind: CharacterKind;
  initiative: string;
  maxHp: string;
  hp: string;
  monsterStats: MonsterStats | null;
  monsterDefinitionId?: string;
}

export function newDraft(kind: CharacterKind = 'player'): CharacterDraft {
  return { name: '', kind, initiative: '0', maxHp: '10', hp: '', monsterStats: null };
}

export interface Confirmation {
  title: string;
  message: string;
  confirmLabel: string;
  resolve: (confirmed: boolean) => void;
}

interface SessionState {
  selectedId: string | null;
  editId: string | null;
  draft: CharacterDraft;
  copied: CharacterInput | null;
  pickerOpen: boolean;
  filter: CharacterKind | 'all';
  hpAmount: string;
  formError: string;
  message: string;
  confirmation: Confirmation | null;
}

export const useSessionStore = create<SessionState>(() => ({
  selectedId: null, editId: null, draft: newDraft(), copied: null,
  pickerOpen: false, filter: 'all', hpAmount: '1', formError: '', message: '', confirmation: null,
}));

export function askConfirmation(title: string, message: string, confirmLabel = '确认'): Promise<boolean> {
  if (useSessionStore.getState().confirmation) return Promise.resolve(false);
  return new Promise((resolve) => useSessionStore.setState({ confirmation: { title, message, confirmLabel, resolve } }));
}

export function resolveConfirmation(confirmed: boolean) {
  const current = useSessionStore.getState().confirmation;
  useSessionStore.setState({ confirmation: null });
  current?.resolve(confirmed);
}
