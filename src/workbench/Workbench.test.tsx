import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../app/App';
import { panelSizes, useWorkbenchStore } from '../stores/workbenchStore';

describe('Workbench Shell', () => {
  it('switches views and panels with initially empty combat', async () => {
    const user = userEvent.setup();
    render(<App />);
    expect(screen.getByRole('main', { name: '战斗' })).toBeInTheDocument();
    expect(screen.queryByRole('complementary', { name: '参战者档案' })).not.toBeInTheDocument();
    const start = screen.getByRole('button', { name: '开始战斗' });
    expect(start).toBeDisabled();
    expect(start).toHaveAccessibleDescription(/请先添加参战者/);
    await user.click(screen.getByRole('button', { name: '角色' }));
    expect(screen.getByRole('main', { name: '角色' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '角色' })).toHaveAttribute('aria-pressed', 'true');
    await user.click(screen.getByRole('button', { name: '怪物图鉴' }));
    expect(screen.getByRole('region', { name: '怪物图鉴' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '切换参战者档案' }));
    expect(screen.getByRole('complementary', { name: '参战者档案' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '关闭参战者档案' }));
    expect(screen.queryByRole('complementary', { name: '参战者档案' })).not.toBeInTheDocument();
    expect(screen.queryByRole('complementary', { name: '主侧栏' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '切换主侧栏' })).not.toBeInTheDocument();
    expect(screen.getAllByText('Dungeon Master Studio')).toHaveLength(1);
    expect(screen.queryByText('仅内存，关闭或刷新后丢失')).not.toBeInTheDocument();
  });

  it('supports bounded keyboard resizing of the inspector', () => {
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: '切换参战者档案' }));
    const inspector = screen.getByRole('separator', { name: '调整参战者档案宽度' });
    expect(inspector).toHaveAttribute('aria-valuenow', '320');
    fireEvent.keyDown(inspector, { key: 'ArrowLeft' });
    expect(inspector).toHaveAttribute('aria-valuenow', '328');
    fireEvent.keyDown(inspector, { key: 'ArrowRight', shiftKey: true });
    expect(inspector).toHaveAttribute('aria-valuenow', '296');
    fireEvent.keyDown(inspector, { key: 'Home' });
    expect(inspector).toHaveAttribute('aria-valuenow', String(panelSizes.inspector.min));
    fireEvent.keyDown(inspector, { key: 'End' });
    expect(inspector).toHaveAttribute('aria-valuenow', String(panelSizes.inspector.max));
  });

  it('resizes from the initial pointer and releases capture', () => {
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: '切换参战者档案' }));
    const separator = screen.getByRole('separator', { name: '调整参战者档案宽度' });
    separator.setPointerCapture = vi.fn();
    separator.releasePointerCapture = vi.fn();
    // jsdom has no native PointerEvent on some Node versions.
    function pointer(type: string, x: number) {
      const event = new Event(type, { bubbles: true });
      Object.assign(event, { clientX: x, pointerId: 1, button: 0 });
      fireEvent(separator, event);
    }
    pointer('pointerdown', 320);
    pointer('pointermove', 300);
    expect(separator).toHaveAttribute('aria-valuenow', '340');
    pointer('pointermove', 310);
    expect(separator).toHaveAttribute('aria-valuenow', '330');
    pointer('pointerup', 310);
    pointer('pointermove', 280);
    expect(separator).toHaveAttribute('aria-valuenow', '330');
    expect(separator.releasePointerCapture).toHaveBeenCalledWith(1);
  });

  it('clamps panel sizes and rejects non-finite widths', () => {
    const store = useWorkbenchStore.getState();
    store.resizePanel('inspector', -100);
    expect(useWorkbenchStore.getState().inspectorWidth).toBe(panelSizes.inspector.min);
    store.resizePanel('inspector', 10000);
    expect(useWorkbenchStore.getState().inspectorWidth).toBe(panelSizes.inspector.max);
    store.resizePanel('inspector', NaN);
    expect(useWorkbenchStore.getState().inspectorWidth).toBe(panelSizes.inspector.max);
  });
});
