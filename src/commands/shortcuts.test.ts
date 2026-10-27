import { describe, expect, it, vi } from 'vitest';
import { installShortcuts } from './shortcuts';
import { createCommands } from './createCommands';
import { useWorkbenchStore } from '../stores/workbenchStore';

function send(target: EventTarget, overrides: KeyboardEventInit = {}) {
  const event = new KeyboardEvent('keydown', {
    key: 'i', shiftKey: true, metaKey: true, bubbles: true, cancelable: true, ...overrides,
  });
  target.dispatchEvent(event);
  return event;
}

describe('workspace shortcuts', () => {
  it('uses the same registry and cleans up its listener', () => {
    const registry = createCommands();
    const execute = vi.spyOn(registry, 'execute');
    const dispose = installShortcuts(registry);
    try {
      expect(send(window).defaultPrevented).toBe(true);
      expect(execute).toHaveBeenCalledWith('workbench.toggleInspector');
      send(window, { key: '3', shiftKey: false, metaKey: false, ctrlKey: true });
      expect(useWorkbenchStore.getState().activeView).toBe('monsters');
      dispose();
      execute.mockClear();
      send(window);
      expect(execute).not.toHaveBeenCalled();
    } finally { dispose(); }
  });

  it('does not override text entry, editable descendants, IME or consumed events', () => {
    const registry = createCommands();
    const execute = vi.spyOn(registry, 'execute');
    const dispose = installShortcuts(registry);
    const container = document.createElement('div');
    container.innerHTML = '<input /><textarea></textarea><select></select><div contenteditable="true"><span>文字</span></div><div role="textbox"></div>';
    document.body.append(container);
    try {
      for (const element of container.querySelectorAll('input, textarea, select, span, [role="textbox"]')) {
        expect(send(element).defaultPrevented).toBe(false);
      }
      send(window, { isComposing: true });
      send(window, { keyCode: 229 });
      send(window, { repeat: true });
      send(window, { altKey: true });
      const consumed = new KeyboardEvent('keydown', { key: 'i', shiftKey: true, metaKey: true, cancelable: true });
      consumed.preventDefault();
      window.dispatchEvent(consumed);
      expect(execute).not.toHaveBeenCalled();
    } finally { dispose(); container.remove(); }
  });

  it('leaves unrelated keyboard combinations to the host', () => {
    const dispose = installShortcuts(createCommands());
    try {
      expect(send(window, { metaKey: false }).defaultPrevented).toBe(false);
      expect(send(window, { key: 'c' }).defaultPrevented).toBe(false);
      expect(send(window, { key: 'b', shiftKey: true }).defaultPrevented).toBe(false);
    } finally { dispose(); }
  });
});
