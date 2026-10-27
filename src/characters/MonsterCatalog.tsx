import { useEffect, useMemo, useRef, useState } from 'react';
import { useCommands } from '../commands/CommandProvider';
import { CommandButton } from '../commands/CommandButton';
import { ensureHandbook, useHandbookStore } from '../stores/handbookStore';
import { searchMonsters } from './handbook';
import { MonsterDetails } from './MonsterDetails';
import { IconButton } from '../components/IconButton';
import type { MonsterDefinition } from './models';
import styles from './Characters.module.css';

export function MonsterCatalog() {
  const { monsters, recent, status, error } = useHandbookStore();
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const registry = useCommands();
  const listRef = useRef<HTMLDivElement>(null);
  const matches = useMemo(() => searchMonsters(monsters, query), [monsters, query]);
  const selected = matches.find((monster) => monster.id === selectedId) ?? matches[0];
  useEffect(() => { void ensureHandbook(); }, []);
  useEffect(() => {
    listRef.current?.querySelector<HTMLElement>('[aria-selected="true"]')?.scrollIntoView?.({ block: 'nearest' });
  }, [selected?.id]);
  function choose(monster: MonsterDefinition) { void registry.execute('monster.choose', monster); }
  return <section className={styles.catalog} aria-label="怪物图鉴">
    <div className={styles.catalogSearch}><label className={styles.field}><span>搜索怪物名（中文或英文）</span>
      <input type="search" value={query} onChange={(event) => { setQuery(event.target.value); setSelectedId(null); }}
        onKeyDown={(event) => {
          if (event.nativeEvent.isComposing) return;
          if (event.key === 'Enter' && selected) { event.preventDefault(); choose(selected); }
          if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            const index = matches.findIndex((monster) => monster.id === selected?.id);
            setSelectedId(matches[Math.max(0, Math.min(matches.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)))]?.id ?? null);
          }
        }} /></label><CommandButton id="character.addManualMonster" text /></div>
    {recent.length > 0 && <div className={styles.recent} aria-label="最近使用"><span>最近使用</span>{recent.map((monster) =>
      <button key={monster.id} type="button" onClick={() => choose(monster)}>{monster.name}</button>)}</div>}
    {status === 'loading' && <p role="status">正在读取本地图鉴…</p>}
    {status === 'error' && <div role="alert"><p>{error}</p><CommandButton id="monster.retry" text /></div>}
    {status === 'ready' && <><p className={styles.muted}>共 {monsters.length} 条 · 匹配 {matches.length} 条</p>
      <div className={styles.catalogBody}><div ref={listRef} className={styles.catalogList} role="listbox" aria-label="怪物搜索结果">
        {!matches.length && <p>没有匹配的怪物</p>}
        {matches.map((monster) => <button key={monster.id} type="button" role="option" tabIndex={selected?.id === monster.id ? 0 : -1} aria-selected={selected?.id === monster.id}
          onClick={() => setSelectedId(monster.id)} onDoubleClick={() => choose(monster)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') { event.preventDefault(); choose(monster); }
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
              event.preventDefault();
              const index = matches.indexOf(monster), next = matches[Math.max(0, Math.min(matches.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)))];
              setSelectedId(next.id);
              const options = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="option"]');
              options?.[matches.indexOf(next)]?.focus();
            }
          }}><span>{monster.name}</span><small>{monster.englishName}</small></button>)}
      </div><div className={styles.catalogDetails}>{selected && <>
        <h3>{selected.name}</h3><p>{selected.creatureType} · 生命值 {selected.maxHp ?? '未知'} · CR {selected.challengeRating}</p>
        <IconButton icon="check" label={`选用 ${selected.name}`} onClick={() => choose(selected)}>选用 {selected.name}</IconButton>
        <MonsterDetails stats={selected.stats} />
      </>}</div></div></>}
  </section>;
}
