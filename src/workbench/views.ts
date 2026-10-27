import type { WorkbenchView } from '../stores/workbenchStore';
import type { IconName } from '../icons/Icon';

export const views: Record<WorkbenchView, { title: string; subtitle: string; icon: IconName }> = {
  combat: { title: '战斗', subtitle: '当前遭遇', icon: 'dice' },
  characters: { title: '角色', subtitle: '玩家与 NPC', icon: 'characters' },
  monsters: { title: '怪物图鉴', subtitle: '本地怪物资料', icon: 'book' },
};
