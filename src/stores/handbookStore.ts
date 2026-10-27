import { create } from 'zustand';
import type { MonsterDefinition } from '../characters/models';
import { loadHandbook } from '../characters/handbook';

interface HandbookState {
  monsters: MonsterDefinition[];
  recent: MonsterDefinition[];
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string;
}
export const useHandbookStore = create<HandbookState>(() => ({ monsters: [], recent: [], status: 'idle', error: '' }));

export async function ensureHandbook(retry = false, loader = loadHandbook) {
  const { status } = useHandbookStore.getState();
  if (status === 'loading' || status === 'ready' || status === 'error' && !retry) return;
  useHandbookStore.setState({ status: 'loading', error: '' });
  try {
    const monsters = await loader();
    useHandbookStore.setState({ monsters, status: 'ready' });
  } catch (error) {
    useHandbookStore.setState({ status: 'error', error: `无法读取本地怪物图鉴：${error instanceof Error ? error.message : '未知错误'}` });
  }
}

export function recordRecent(monster: MonsterDefinition) {
  useHandbookStore.setState((state) => ({ recent: [monster, ...state.recent.filter((entry) => entry.id !== monster.id)].slice(0, 6) }));
}
