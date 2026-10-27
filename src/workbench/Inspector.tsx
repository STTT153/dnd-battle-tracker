import { IconButton } from '../components/IconButton';
import { useCommands } from '../commands/CommandProvider';
import { useSessionStore } from '../stores/sessionStore';
import { CharacterForm } from '../characters/CharacterForm';
import { kindLabels } from '../characters/models';
import styles from './Workbench.module.css';

export function Inspector() {
  const registry = useCommands();
  const { draft, editId } = useSessionStore();
  return <aside className={styles.inspector} id="combatant-inspector" aria-label="参战者档案">
    <div className={styles.panelHeading}><span>{editId ? draft.name : `添加${kindLabels[draft.kind]}`}</span>
      <IconButton icon="close" label="关闭参战者档案" onClick={() => { void registry.execute('workbench.toggleInspector'); }} />
    </div>
    <div className={styles.inspectorBody}><CharacterForm /></div>
  </aside>;
}
