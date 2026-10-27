import { CommandButton } from '../commands/CommandButton';
import { Icon } from '../icons/Icon';
import { useWorkbenchStore } from '../stores/workbenchStore';
import styles from './Workbench.module.css';

export function ActivityBar() {
  const view = useWorkbenchStore((state) => state.activeView);
  return <nav className={styles.activityBar} aria-label="工作区视图">
    {(['combat', 'characters', 'monsters'] as const).map((id) =>
      <CommandButton key={id} id={`workbench.view.${id}`} pressed={view === id} className={styles.activityButton} />)}
    <div className={styles.activityFooter}><Icon name="shield" /></div>
  </nav>;
}
