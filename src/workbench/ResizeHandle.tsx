import { useRef, type KeyboardEvent, type PointerEvent } from 'react';
import { panelSizes, useWorkbenchStore, type Panel } from '../stores/workbenchStore';
import styles from './Workbench.module.css';

export function ResizeHandle({ panel, controls }: { panel: Panel; controls: string }) {
  const width = useWorkbenchStore((state) => state.inspectorWidth);
  const resize = useWorkbenchStore((state) => state.resizePanel);
  const drag = useRef<{ x: number; width: number; pointerId: number } | null>(null);
  const direction = -1;
  const bounds = panelSizes[panel];
  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const step = event.shiftKey ? 32 : 8;
    let next: number;
    if (event.key === 'ArrowLeft') next = width - step * direction;
    else if (event.key === 'ArrowRight') next = width + step * direction;
    else if (event.key === 'Home') next = bounds.min;
    else if (event.key === 'End') next = bounds.max;
    else return;
    event.preventDefault();
    resize(panel, next);
  }
  function onPointerDown(event: PointerEvent<HTMLDivElement>) {
    if (event.button !== 0) return;
    drag.current = { x: event.clientX, width, pointerId: event.pointerId };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.currentTarget.focus();
    event.preventDefault();
  }
  return <div role="separator" tabIndex={0} aria-orientation="vertical"
    aria-label="调整参战者档案宽度"
    aria-controls={controls} aria-valuemin={bounds.min} aria-valuemax={bounds.max}
    aria-valuenow={width} className={styles.resizeHandle} onKeyDown={onKeyDown}
    onPointerDown={onPointerDown} onPointerMove={(event) => {
      if (!drag.current || drag.current.pointerId !== event.pointerId) return;
      resize(panel, drag.current.width + direction * (event.clientX - drag.current.x));
    }} onPointerUp={(event) => {
      if (drag.current?.pointerId === event.pointerId) {
        drag.current = null;
        event.currentTarget.releasePointerCapture(event.pointerId);
      }
    }} onLostPointerCapture={() => { drag.current = null; }}
    onPointerCancel={() => { drag.current = null; }} />;
}
