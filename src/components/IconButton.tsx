import { Icon, type IconName } from '../icons/Icon';
import styles from './IconButton.module.css';

export function IconButton({ icon, label, disabled = false, disabledReason, pressed,
  onClick, className = '', children, type = 'button' }: {
  icon: IconName;
  label: string;
  disabled?: boolean;
  disabledReason?: string;
  pressed?: boolean;
  onClick: () => void;
  className?: string;
  children?: React.ReactNode;
  type?: 'button' | 'submit';
}) {
  const description = disabled && disabledReason ? `${label}：${disabledReason}` : label;
  return <span className={styles.wrapper} title={description}>
    <button type={type} className={`${styles.button} ${className}`}
      aria-label={label} aria-description={disabled ? disabledReason : undefined}
      aria-pressed={pressed} disabled={disabled} onClick={onClick}>
      <Icon name={icon} />{children}
    </button>
  </span>;
}
