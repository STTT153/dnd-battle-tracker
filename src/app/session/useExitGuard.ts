import { useEffect } from 'react';
import { isTauri, invoke } from '@tauri-apps/api/core';
import { installExitGuard, type SessionBridge } from './exitGuard';
import { useSessionStore } from '../../stores/sessionStore';

let bridgePromise: Promise<SessionBridge> | undefined;
function nativeBridge() {
  bridgePromise ??= import('@tauri-apps/api/event').then(({ listen }) => {
    let pending = Promise.resolve();
    return {
      setGuard: (enabled: boolean) => {
        // Keep StrictMode setup/cleanup and rapid empty/non-empty transitions ordered.
        const next = pending.then(() => invoke<void>('session_set_close_guard', { enabled }));
        pending = next.catch(() => {});
        return next;
      },
      listenExit: (callback: () => void) => listen('session:request-exit', callback),
      confirmExit: () => invoke<void>('session_confirm_exit'),
    };
  });
  return bridgePromise;
}

export function useExitGuard() {
  useEffect(() => {
    let disposed = false;
    let stop = installExitGuard(null);
    if (isTauri()) void nativeBridge().then((bridge) => {
      if (disposed) return;
      stop();
      stop = installExitGuard(bridge);
    }).catch(() => { if (!disposed) useSessionStore.setState({ message: '无法启用桌面退出确认，请勿关闭当前内存战斗。' }); });
    return () => { disposed = true; stop(); };
  }, []);
}
