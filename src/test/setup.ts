import '@testing-library/jest-dom/vitest';
import { afterEach, beforeEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import { useWorkbenchStore } from '../stores/workbenchStore';
import { useSessionStore, resolveConfirmation } from '../stores/sessionStore';
import { useHandbookStore } from '../stores/handbookStore';
import { useCombatStore } from '../stores/combatStore';

beforeEach(() => {
  useWorkbenchStore.setState(useWorkbenchStore.getInitialState(), true);
  useSessionStore.setState(useSessionStore.getInitialState(), true);
  useHandbookStore.setState(useHandbookStore.getInitialState(), true);
  useCombatStore.setState(useCombatStore.getInitialState(), true);
});
afterEach(() => { cleanup(); resolveConfirmation(false); });
