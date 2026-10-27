import { describe, expect, it, vi } from 'vitest';
import { installExitGuard, type SessionBridge } from './exitGuard';
import { useCombatStore } from '../../stores/combatStore';
import { resolveConfirmation, useSessionStore } from '../../stores/sessionStore';
import { addCharacter, emptyEncounter } from '../../characters/rules';
import { player } from '../../test/fixtures';

const flush = async () => { await Promise.resolve(); await Promise.resolve(); };
function nativeMock() {
  let onExit = () => {};
  const unlisten = vi.fn();
  const bridge: SessionBridge = {
    setGuard: vi.fn(async () => {}),
    listenExit: vi.fn(async (callback) => { onExit = callback; return unlisten; }),
    confirmExit: vi.fn(async () => {}),
  };
  return { bridge, request: () => onExit(), unlisten };
}
function addActor() {
  useCombatStore.setState({ encounter: addCharacter(emptyEncounter(), player, 'a') });
}

describe('memory session exit protection', () => {
  it('only blocks unload when participants exist and cleans its listener', () => {
    const stop = installExitGuard(null);
    const unload = () => {
      const event = new Event('beforeunload', { cancelable: true });
      window.dispatchEvent(event);
      return event.defaultPrevented;
    };
    expect(unload()).toBe(false);
    addActor();
    expect(unload()).toBe(true);
    useCombatStore.setState({ encounter: emptyEncounter() });
    expect(unload()).toBe(false);
    addActor(); stop();
    expect(unload()).toBe(false);
  });
  it('mirrors only presence, cancels without losing data and confirms exit once', async () => {
    const native = nativeMock();
    const stop = installExitGuard(native.bridge);
    await flush();
    expect(native.bridge.setGuard).toHaveBeenLastCalledWith(false);
    addActor();
    expect(native.bridge.setGuard).toHaveBeenLastCalledWith(true);
    native.request(); native.request();
    expect(useSessionStore.getState().confirmation?.title).toBe('退出内存战斗');
    resolveConfirmation(false); await flush();
    expect(native.bridge.confirmExit).not.toHaveBeenCalled();
    expect(useCombatStore.getState().encounter.combatants).toHaveLength(1);
    native.request(); resolveConfirmation(true); await flush();
    expect(native.bridge.confirmExit).toHaveBeenCalledOnce();
    stop(); expect(native.unlisten).toHaveBeenCalledOnce();
  });
  it('allows a stale native close event after combat has been cleared', async () => {
    const native = nativeMock(); addActor();
    const stop = installExitGuard(native.bridge); await flush();
    useCombatStore.setState({ encounter: emptyEncounter() });
    expect(native.bridge.setGuard).toHaveBeenLastCalledWith(false);
    native.request(); await flush();
    expect(native.bridge.confirmExit).toHaveBeenCalledOnce();
    expect(useSessionStore.getState().confirmation).toBeNull();
    stop();
  });
  it('unsubscribes late native listeners and reports native setup errors', async () => {
    const late = vi.fn();
    let resolve: (stop: () => void) => void = () => {};
    const bridge = nativeMock().bridge;
    bridge.listenExit = () => new Promise((callback) => { resolve = callback; });
    const stop = installExitGuard(bridge); stop(); resolve(late); await flush();
    expect(late).toHaveBeenCalledOnce();
    const failed = nativeMock().bridge;
    failed.listenExit = async () => { throw new Error('权限错误'); };
    const dispose = installExitGuard(failed); await flush();
    expect(useSessionStore.getState().message).toContain('权限错误');
    dispose();
  });
});
