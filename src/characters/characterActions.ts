import type { CharacterInput, CharacterKind, MonsterDefinition } from './models';
import { addCharacter, BattleError, displayName, editCharacter, getActor, removeCharacter } from './rules';
import { useCombatStore } from '../stores/combatStore';
import { newDraft, useSessionStore } from '../stores/sessionStore';
import { useWorkbenchStore } from '../stores/workbenchStore';

export function showInspector() {
  useWorkbenchStore.setState({ inspectorVisible: true });
}

export function prepareCharacter(kind: CharacterKind) {
  useSessionStore.setState({ draft: newDraft(kind), selectedId: null, editId: null, formError: '', message: '' });
  showInspector();
}

export function selectCharacter(id: string) {
  const actor = getActor(useCombatStore.getState().encounter, id);
  useSessionStore.setState({ selectedId: id, editId: id, formError: '', draft: {
    name: actor.name, kind: actor.kind, initiative: String(actor.initiative),
    maxHp: String(actor.maxHp), hp: String(actor.hp), monsterStats: structuredClone(actor.monsterStats),
    monsterDefinitionId: actor.monsterDefinitionId,
  } });
  showInspector();
}

function parseInteger(text: string, label: string) {
  if (!/^[+-]?\d+$/.test(text.trim())) throw new BattleError(`${label}请输入整数，不能留空或填写小数。`);
  return Number(text.trim());
}

export function submitCharacter() {
  const { draft, editId } = useSessionStore.getState();
  useSessionStore.setState({ message: '' });
  try {
    const maxHp = parseInteger(draft.maxHp, '最大生命值');
    const input: CharacterInput = { ...draft, maxHp,
      initiative: parseInteger(draft.initiative, '先攻值'),
      hp: editId === null && !draft.hp.trim() ? maxHp : parseInteger(draft.hp, '当前生命值'),
    };
    const encounter = useCombatStore.getState().encounter;
    const id = editId ?? crypto.randomUUID();
    const next = editId ? editCharacter(encounter, id, input) : addCharacter(encounter, input, id);
    useCombatStore.setState({ encounter: next });
    selectCharacter(id);
    useSessionStore.setState({ message: `${editId ? '已更新' : '已添加'} ${displayName(getActor(next, id))}` });
    useWorkbenchStore.setState({ activeView: 'combat' });
    return true;
  } catch (error) {
    if (!(error instanceof BattleError)) throw error;
    useSessionStore.setState({ formError: error.message });
    return false;
  }
}

export function removeSelected(id: string) {
  const encounter = useCombatStore.getState().encounter;
  const name = displayName(getActor(encounter, id));
  const filter = useSessionStore.getState().filter;
  const visible = encounter.combatants.filter((actor) => useWorkbenchStore.getState().activeView !== 'characters'
    || filter === 'all' || actor.kind === filter);
  const rows = visible.some((actor) => actor.id === id) ? visible : encounter.combatants;
  const index = rows.findIndex((actor) => actor.id === id);
  const nextId = rows[index + 1]?.id ?? rows[index - 1]?.id;
  const next = removeCharacter(encounter, id);
  useCombatStore.setState({ encounter: next });
  if (nextId) selectCharacter(nextId);
  else useSessionStore.setState({ selectedId: null, editId: null, draft: newDraft(), formError: '' });
  useSessionStore.setState({ message: `已移除 ${name}` });
}

export function chooseMonster(monster: MonsterDefinition) {
  prepareCharacter('monster');
  useSessionStore.setState({ pickerOpen: false, draft: {
    ...newDraft('monster'), name: monster.name, maxHp: String(monster.maxHp ?? 10),
    monsterStats: structuredClone(monster.stats), monsterDefinitionId: monster.id,
  } });
}
