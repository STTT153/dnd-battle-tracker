import { Icon } from '../icons/Icon';
import { useCombatStore } from '../stores/combatStore';
import styles from './Workbench.module.css';

export function StatusBar() {
  const count = useCombatStore((state) => state.encounter.combatants.length);
  const round = useCombatStore((state) => state.encounter.round);
  return <footer className={styles.statusBar} aria-label="工作区状态">
    <div className={styles.statusGroup}><Icon name="shield" /><span>本地工作区</span><span>参战人数: {count}</span><span>回合数: {round}</span></div>
    <div className={styles.statusGroup}><span>仅内存</span><span>关闭后丢失</span><Icon name="check" /></div>
  </footer>;
}
