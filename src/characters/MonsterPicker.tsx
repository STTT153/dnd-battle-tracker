import { useSessionStore } from '../stores/sessionStore';
import { useCommands } from '../commands/CommandProvider';
import { CommandButton } from '../commands/CommandButton';
import { Modal } from '../components/Modal';
import { MonsterCatalog } from './MonsterCatalog';

export function MonsterPicker() {
  const open = useSessionStore((state) => state.pickerOpen);
  const registry = useCommands();
  if (!open) return null;
  return <Modal wide title="选择怪物" onClose={() => { void registry.execute('monster.closePicker'); }}>
    <MonsterCatalog /><CommandButton id="monster.closePicker" text />
  </Modal>;
}
