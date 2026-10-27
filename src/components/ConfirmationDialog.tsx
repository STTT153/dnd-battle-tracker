import { resolveConfirmation, useSessionStore } from '../stores/sessionStore';
import { IconButton } from './IconButton';
import { Modal } from './Modal';
import styles from './Modal.module.css';

export function ConfirmationDialog() {
  const confirmation = useSessionStore((state) => state.confirmation);
  if (!confirmation) return null;
  return <Modal title={confirmation.title} onClose={() => resolveConfirmation(false)}>
    <p>{confirmation.message}</p>
    <div className={styles.actions}>
      <IconButton icon="close" label="取消" onClick={() => resolveConfirmation(false)}>取消</IconButton>
      <IconButton icon="check" label={confirmation.confirmLabel} onClick={() => resolveConfirmation(true)}>{confirmation.confirmLabel}</IconButton>
    </div>
  </Modal>;
}
