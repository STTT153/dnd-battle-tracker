import { useEffect } from 'react';
import { useSessionStore } from '../stores/sessionStore';
import type { SimpleCommandId, CommandRegistry } from './registry';

function isEditing(event: KeyboardEvent): boolean {
  return event.composedPath().some((target) => target instanceof HTMLElement && (
    target.matches('input, textarea, select, [role="textbox"]') || target.isContentEditable
    || (target.hasAttribute('contenteditable') && target.getAttribute('contenteditable') !== 'false')
  ));
}

export function installShortcuts(registry: CommandRegistry, target: Window = window) {
  const onKeyDown = (event: KeyboardEvent) => {
    if (event.defaultPrevented || event.isComposing || event.keyCode === 229
      || event.repeat || isEditing(event) || event.altKey) return;
    if (!(event.metaKey || event.ctrlKey)) return;
    if (useSessionStore.getState().confirmation || useSessionStore.getState().pickerOpen) return;
    let id: SimpleCommandId | undefined;
    if (event.shiftKey && event.key.toLowerCase() === 'i') id = 'workbench.toggleInspector';
    if (!event.shiftKey) {
      const view = ({ '1': 'combat', '2': 'characters', '3': 'monsters' } as const)[event.key as '1' | '2' | '3'];
      if (view) id = `workbench.view.${view}`;
    }
    if (!event.shiftKey) {
      const key = event.key.toLowerCase();
      if (key === 'c') id = 'character.copy';
      if (key === 'v') id = 'character.paste';
      const mac = /Mac|iPhone|iPad/.test(navigator.platform);
      if (mac && event.metaKey && ['Backspace', 'Delete'].includes(event.key)
        || !mac && event.ctrlKey && event.key === 'Delete') id = 'character.quickRemove';
    }
    if (id && registry.getAvailability(id).enabled) {
      event.preventDefault();
      void registry.execute(id);
    }
  };
  target.addEventListener('keydown', onKeyDown);
  return () => target.removeEventListener('keydown', onKeyDown);
}

export function useShortcuts(registry: CommandRegistry) {
  useEffect(() => installShortcuts(registry), [registry]);
}
