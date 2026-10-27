import type { CSSProperties } from 'react';
import { useWorkbenchStore } from '../stores/workbenchStore';
import { ActivityBar } from './ActivityBar';
import { Toolbar } from './Toolbar';
import { MainContent } from './MainContent';
import { Inspector } from './Inspector';
import { ResizeHandle } from './ResizeHandle';
import { StatusBar } from './StatusBar';
import { MonsterPicker } from '../characters/MonsterPicker';
import { ConfirmationDialog } from '../components/ConfirmationDialog';
import styles from './Workbench.module.css';

export function Workbench() {
  const { inspectorVisible, inspectorWidth } = useWorkbenchStore();
  const columns = [
    'var(--activity-bar-width)',
    'minmax(0, 1fr)',
    ...(inspectorVisible ? ['var(--resize-width)', `${inspectorWidth}px`] : []),
  ].join(' ');
  return <div className={styles.workbench}>
    <a className={styles.skipLink} href="#main-content">跳转到主内容</a>
    <header className={styles.titleBar}><span>Dungeon Master Studio</span></header>
    <Toolbar />
    <div className={styles.workspace} style={{ '--workspace-columns': columns } as CSSProperties}>
      <ActivityBar />
      <MainContent />
      {inspectorVisible && <><ResizeHandle panel="inspector" controls="combatant-inspector" /><Inspector /></>}
    </div>
    <StatusBar />
    <MonsterPicker />
    <ConfirmationDialog />
  </div>;
}
