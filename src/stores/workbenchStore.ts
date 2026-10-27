import { create } from 'zustand';

export type WorkbenchView = 'combat' | 'characters' | 'monsters';
export type Panel = 'inspector';

export const panelSizes = {
  inspector: { initial: 320, min: 240, max: 360 },
} as const;

interface WorkbenchState {
  activeView: WorkbenchView;
  inspectorVisible: boolean;
  inspectorWidth: number;
  setView: (view: WorkbenchView) => void;
  togglePanel: (panel: Panel) => void;
  resizePanel: (panel: Panel, width: number) => void;
}

export const useWorkbenchStore = create<WorkbenchState>((set) => ({
  activeView: 'combat',
  inspectorVisible: false,
  inspectorWidth: panelSizes.inspector.initial,
  setView: (activeView) => set({ activeView }),
  togglePanel: () => set((state) => ({ inspectorVisible: !state.inspectorVisible })),
  resizePanel: (panel, width) => {
    if (!Number.isFinite(width)) return;
    const bounds = panelSizes[panel];
    const clamped = Math.round(Math.max(bounds.min, Math.min(bounds.max, width)));
    set({ inspectorWidth: clamped });
  },
}));
