import type { CSSProperties } from 'react';

const codicons = {
  play: 'play', next: 'debug-step-over', reset: 'clear-all', stop: 'debug-stop',
  addPlayer: 'person-add', close: 'close',
  inspector: 'layout-sidebar-right', characters: 'organization',
  book: 'book', chevron: 'chevron-down', check: 'check', shield: 'shield',
  edit: 'edit', copy: 'copy', paste: 'clippy', trash: 'trash', filter: 'filter',
  sort: 'sort-precedence', up: 'arrow-up', down: 'arrow-down', damage: 'remove', heal: 'add',
} as const;

const dndPaths = {
  dice: 'M8 1 14.5 4.5v7L8 15l-6.5-3.5v-7L8 1Zm0 0L5 5l-3.5-.5M8 1l3 4 3.5-.5M5 5h6l2 6-5 4-5-4 2-6Zm0 0 3 6 3-6m-8 6h10',
  monster: 'M3 6 2 2l4 2h4l4-2-1 4v5l-3 3H6l-3-3V6Zm2 2h1m4 0h1M6 11l2 1 2-1',
} as const;

export type IconName = keyof typeof codicons | keyof typeof dndPaths;

export function Icon({ name, className = '', style }: {
  name: IconName; className?: string; style?: CSSProperties;
}) {
  if (name in dndPaths) {
    return <svg className={`dnd-icon ${className}`} style={style} viewBox="0 0 16 16"
      fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"
      strokeLinecap="round" aria-hidden="true" focusable="false">
      <path d={dndPaths[name as keyof typeof dndPaths]} />
    </svg>;
  }
  return <span aria-hidden="true" style={style}
    className={`codicon codicon-${codicons[name as keyof typeof codicons]} ${className}`} />;
}
