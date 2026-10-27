import { CombatView } from '../combat/CombatView';
import { CharacterView } from '../characters/CharacterView';
import { MonsterCatalog } from '../characters/MonsterCatalog';
import { Icon } from '../icons/Icon';
import { useWorkbenchStore } from '../stores/workbenchStore';
import { useSessionStore } from '../stores/sessionStore';
import { views } from './views';
import styles from './Workbench.module.css';

export function MainContent() {
  const view = useWorkbenchStore((state) => state.activeView);
  const message = useSessionStore((state) => state.message);
  return <main className={styles.main} id="main-content" tabIndex={-1} aria-label={views[view].title}>
    <div className={styles.editorTabs}><div className={styles.activeTab}><Icon name={views[view].icon} /><span>{views[view].title}</span></div></div>
    {message && <div className={styles.message} role="status">{message}</div>}
    <div className={styles.mainScroll}>
      {view === 'combat' ? <CombatView /> : view === 'characters' ? <CharacterView /> : <MonsterCatalog />}
    </div>
  </main>;
}
