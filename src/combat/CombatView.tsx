import { CommandButton } from '../commands/CommandButton';
import { useCombatStore } from '../stores/combatStore';
import { useSessionStore } from '../stores/sessionStore';
import { useCommands } from '../commands/CommandProvider';
import { CombatantTable } from '../characters/CombatantTable';
import styles from '../workbench/Workbench.module.css';

export function CombatView() {
  const encounter = useCombatStore((state) => state.encounter);
  const amount = useSessionStore((state) => state.hpAmount);
  const registry = useCommands();
  return <section className={styles.combatView} aria-label="战斗工作区">
    <div className={styles.contentHeading}><div><h1>战斗工作区</h1><p>选择参战者以编辑档案或操作血量。</p></div><span className={styles.badge}>{!encounter.active ? '准备阶段' : encounter.currentId ? `第 ${encounter.round} 轮` : '本轮已结束'}</span></div>
    <div className={styles.listActions}><CommandButton id="character.addPlayer" text /><CommandButton id="character.addNpc" text />
      <CommandButton id="character.addMonster" text /><CommandButton id="character.copy" /><CommandButton id="character.paste" /><CommandButton id="character.remove" /></div>
    <div className={styles.listActions}><CommandButton id="combat.sort" text /><CommandButton id="combat.moveUp" /><CommandButton id="combat.moveDown" /></div>
    <CombatantTable />
    <div className={styles.hpControls}><label>数值 <input aria-label="血量操作数值" inputMode="numeric" value={amount}
      onChange={(event) => { void registry.execute('combat.setAmount', event.target.value); }} /></label>
      <CommandButton id="combat.damage" text /><CommandButton id="combat.heal" text /></div>
  </section>;
}
