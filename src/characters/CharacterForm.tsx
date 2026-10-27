import { useEffect, useRef } from 'react';
import { useCommands } from '../commands/CommandProvider';
import { useSessionStore } from '../stores/sessionStore';
import { kindLabels } from './models';
import { IconButton } from '../components/IconButton';
import { MonsterDetails } from './MonsterDetails';
import styles from './Characters.module.css';

export function CharacterForm() {
  const { draft, editId, formError } = useSessionStore();
  const registry = useCommands();
  const errorRef = useRef<HTMLParagraphElement>(null);
  useEffect(() => { if (formError) errorRef.current?.focus(); }, [formError]);
  return <form className={styles.form} aria-label={editId ? '编辑参战者' : '新增参战者'}
    onSubmit={(event) => { event.preventDefault(); void registry.execute('character.submit'); }}>
    <div className={styles.formFields}>
      <p className={styles.muted}>{kindLabels[draft.kind]}{draft.kind === 'monster' ? ' · 编号由系统自动添加，请填写基础名称' : ''}</p>
      {([['name', '名称'], ['initiative', '先攻值'], ['maxHp', '最大 HP'], ['hp', '当前 HP']] as const).map(([key, label]) =>
        <label key={key} className={styles.field}><span>{label}</span><input name={key} value={draft[key]}
          inputMode={key === 'name' ? 'text' : 'numeric'} autoComplete="off"
          placeholder={key === 'hp' && !editId ? '留空等于最大 HP' : undefined}
          onChange={(event) => { void registry.execute('character.updateDraft', { [key]: event.target.value }); }} /></label>)}
      {formError && <p ref={errorRef} tabIndex={-1} className={styles.error} role="alert">{formError}</p>}
      {draft.kind === 'monster' && draft.monsterStats && <MonsterDetails stats={draft.monsterStats} />}
    </div>
    <div className={styles.formFooter}><IconButton type="submit" icon="check" label={editId ? '保存修改' : '确认添加'} onClick={() => {}}>
      {editId ? '保存修改' : '确认添加'}
    </IconButton></div>
  </form>;
}
