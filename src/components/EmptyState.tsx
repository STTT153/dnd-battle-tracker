import { Icon, type IconName } from '../icons/Icon';
import styles from './EmptyState.module.css';

export function EmptyState({ icon, title, children }: {
  icon: IconName; title: string; children: React.ReactNode;
}) {
  return <section className={styles.empty}>
    <Icon name={icon} className={styles.icon} />
    <h2>{title}</h2>
    <div className={styles.description}>{children}</div>
  </section>;
}
