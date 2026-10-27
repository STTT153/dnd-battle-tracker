import { CommandButton } from '../commands/CommandButton';
import { useCommands } from '../commands/CommandProvider';
import { useSessionStore } from '../stores/sessionStore';
import { CombatantTable } from './CombatantTable';
import { kindLabels, type CharacterKind } from './models';
import styles from './Characters.module.css';

export function CharacterView() {
  const filter = useSessionStore((state) => state.filter);
  const registry = useCommands();
  return <section className={styles.view} aria-label="当前遭遇角色">
    <div className={styles.viewHeading}><h1>当前遭遇角色</h1>
      <label>类型 <select value={filter} onChange={(event) => { void registry.execute('character.filter', event.target.value as CharacterKind | 'all'); }}>
        <option value="all">全部</option>{Object.entries(kindLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select></label>
    </div>
    <div className={styles.actions}><CommandButton id="character.addPlayer" text /><CommandButton id="character.addNpc" text />
      <CommandButton id="character.addMonster" text /><CommandButton id="character.copy" /><CommandButton id="character.paste" /><CommandButton id="character.remove" /></div>
    <CombatantTable filtered />
  </section>;
}
