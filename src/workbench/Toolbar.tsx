import { CommandButton } from '../commands/CommandButton';
import { useWorkbenchStore } from '../stores/workbenchStore';
import styles from './Workbench.module.css';

export function Toolbar() {
  const inspector = useWorkbenchStore((state) => state.inspectorVisible);
  return <div role="toolbar" aria-label="战斗与布局操作" className={styles.toolbar}>
    <div className={styles.toolbarGroup}>
      <CommandButton id="combat.start" /><CommandButton id="combat.nextTurn" />
      <CommandButton id="combat.stop" /><CommandButton id="combat.reset" />
      <span className={styles.divider} />
      <CommandButton id="character.addPlayer" /><CommandButton id="character.addNpc" /><CommandButton id="character.addMonster" />
    </div>
    <div className={styles.toolbarGroup}>
      <CommandButton id="workbench.toggleInspector" pressed={inspector} />
    </div>
  </div>;
}
