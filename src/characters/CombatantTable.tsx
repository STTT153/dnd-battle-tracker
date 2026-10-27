import { useEffect, useRef } from 'react';
import { useCommands } from '../commands/CommandProvider';
import { useCombatStore } from '../stores/combatStore';
import { useSessionStore } from '../stores/sessionStore';
import { displayName } from './rules';
import { kindLabels } from './models';
import { EmptyState } from '../components/EmptyState';
import styles from './Characters.module.css';

export function CombatantTable({ filtered = false }: { filtered?: boolean }) {
  const encounter = useCombatStore((state) => state.encounter);
  const selectedId = useSessionStore((state) => state.selectedId);
  const filter = useSessionStore((state) => state.filter);
  const registry = useCommands();
  const tableRef = useRef<HTMLTableElement>(null);
  const actors = encounter.combatants.filter((actor) => !filtered || filter === 'all' || actor.kind === filter);
  useEffect(() => {
    const button = tableRef.current?.querySelector<HTMLButtonElement>('[aria-pressed="true"]');
    button?.scrollIntoView?.({ block: 'nearest', inline: 'nearest' });
  }, [selectedId, encounter.currentId]);
  if (!actors.length) return <EmptyState icon="dice" title={encounter.combatants.length ? '没有匹配的角色' : '尚未集结队伍'}>
    <p>使用工具栏添加玩家、NPC 或怪物。</p>
  </EmptyState>;
  return <div className={styles.tableViewport}><table ref={tableRef} className={styles.table} aria-label="参战者列表"
    onKeyDown={(event) => {
      if (!['ArrowUp', 'ArrowDown'].includes(event.key) || event.metaKey || event.ctrlKey || event.altKey) return;
      const buttons = [...tableRef.current!.querySelectorAll<HTMLButtonElement>('button')];
      const index = buttons.indexOf(event.target as HTMLButtonElement);
      if (index < 0) return;
      const next = Math.max(0, Math.min(actors.length - 1, index + (event.key === 'ArrowUp' ? -1 : 1)));
      event.preventDefault();
      void registry.execute('character.select', actors[next].id);
      buttons[next].focus();
    }}><thead><tr><th>本轮</th><th>类型</th><th>名称</th><th>先攻</th><th>生命值</th></tr></thead>
    <tbody>{actors.map((actor) => <tr key={actor.id} data-current={actor.id === encounter.currentId}
      onClick={() => { void registry.execute('character.select', actor.id); }}
      data-selected={actor.id === selectedId} data-zero={actor.hp === 0}>
      <td>{actor.id === encounter.currentId ? '行动中' : encounter.actedIds.includes(actor.id) ? '已行动' : encounter.active ? '待行动' : '未开始'}</td>
      <td>{kindLabels[actor.kind]}</td><td><button type="button" aria-pressed={actor.id === selectedId}>{displayName(actor)}</button></td>
      <td>{actor.initiative}</td><td>{actor.hp} / {actor.maxHp}{actor.hp === 0 && <strong className={styles.zero}> · 0 HP</strong>}</td>
    </tr>)}</tbody>
  </table></div>;
}
