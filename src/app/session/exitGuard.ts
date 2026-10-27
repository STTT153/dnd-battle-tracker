import { useCombatStore } from '../../stores/combatStore';
import { askConfirmation, useSessionStore } from '../../stores/sessionStore';

/** The only native boundary here is window lifecycle; no encounter data leaves JS. */
export interface SessionBridge {
  setGuard: (enabled: boolean) => Promise<void>;
  listenExit: (callback: () => void) => Promise<() => void>;
  confirmExit: () => Promise<void>;
}

export function installExitGuard(bridge: SessionBridge | null, target: Window = window) {
  let disposed = false;
  let allowUnload = false;
  let requesting = false;
  let unlisten = () => {};
  const hasActors = () => useCombatStore.getState().encounter.combatants.length > 0;
  const report = (error: unknown) => {
    if (!disposed) useSessionStore.setState({ message: `退出保护未能完成：${error instanceof Error ? error.message : '未知错误'}。请勿关闭窗口。` });
  };
  const beforeUnload = (event: BeforeUnloadEvent) => {
    if (!allowUnload && hasActors()) {
      event.preventDefault();
      event.returnValue = '';
    }
  };
  target.addEventListener('beforeunload', beforeUnload);
  let previous: boolean | undefined;
  const sync = () => {
    const enabled = hasActors();
    if (enabled !== previous) {
      previous = enabled;
      void bridge?.setGuard(enabled).catch(report);
    }
  };
  const unsubscribe = useCombatStore.subscribe(sync);
  if (bridge) {
    void bridge.listenExit(() => {
      if (disposed || requesting || useSessionStore.getState().confirmation) return;
      requesting = true;
      void (async () => {
        if (hasActors() && !await askConfirmation('退出内存战斗', '参战者和战斗进度尚未保存，退出后将全部丢失。确定退出？', '退出')) return;
        if (disposed) return;
        allowUnload = true;
        try { await bridge.confirmExit(); }
        catch (error) { allowUnload = false; report(error); }
      })().finally(() => { requesting = false; });
    }).then((stop) => {
      if (disposed) stop();
      else { unlisten = stop; sync(); }
    }).catch(report);
  }
  return () => {
    disposed = true;
    unsubscribe();
    unlisten();
    target.removeEventListener('beforeunload', beforeUnload);
    if (bridge) void bridge.setGuard(false).catch(() => {});
  };
}
