import * as React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './dialog';
import { Button } from './button';
import { AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-react';

export type ConfirmModalVariant = 'danger' | 'warning' | 'info' | 'success';

interface ConfirmModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel?: () => void;
  variant?: ConfirmModalVariant;
  loading?: boolean;
}

const variantConfig = {
  danger: {
    icon: XCircle,
    iconClass: 'text-red-500',
    buttonClass: 'bg-red-600 hover:bg-red-500 text-white',
  },
  warning: {
    icon: AlertTriangle,
    iconClass: 'text-yellow-500',
    buttonClass: 'bg-yellow-600 hover:bg-yellow-500 text-white',
  },
  info: {
    icon: Info,
    iconClass: 'text-blue-500',
    buttonClass: 'bg-blue-600 hover:bg-blue-500 text-white',
  },
  success: {
    icon: CheckCircle,
    iconClass: 'text-green-500',
    buttonClass: 'bg-green-600 hover:bg-green-500 text-white',
  },
};

export function ConfirmModal({
  open,
  onOpenChange,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  variant = 'danger',
  loading = false,
}: ConfirmModalProps) {
  const config = variantConfig[variant];
  const Icon = config.icon;

  const handleConfirm = () => {
    onConfirm();
    if (!loading) {
      onOpenChange(false);
    }
  };

  const handleCancel = () => {
    onCancel?.();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md glass-card border-white/10">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-white/10 ${config.iconClass}`}>
              <Icon className="h-5 w-5" />
            </div>
            <DialogTitle>{title}</DialogTitle>
          </div>
          {description && (
            <DialogDescription className="mt-2 text-muted-foreground">
              {description}
            </DialogDescription>
          )}
        </DialogHeader>
        <DialogFooter className="mt-4 flex gap-2 sm:gap-2">
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={loading}
            className="glass"
          >
            {cancelText}
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={loading}
            className={config.buttonClass}
          >
            {loading ? 'Processing...' : confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Alert modal for displaying messages (replacement for window.alert)
interface AlertModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmText?: string;
  variant?: ConfirmModalVariant;
}

export function AlertModal({
  open,
  onOpenChange,
  title,
  description,
  confirmText = 'OK',
  variant = 'info',
}: AlertModalProps) {
  const config = variantConfig[variant];
  const Icon = config.icon;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md glass-card border-white/10">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-white/10 ${config.iconClass}`}>
              <Icon className="h-5 w-5" />
            </div>
            <DialogTitle>{title}</DialogTitle>
          </div>
          {description && (
            <DialogDescription className="mt-2 text-muted-foreground">
              {description}
            </DialogDescription>
          )}
        </DialogHeader>
        <DialogFooter className="mt-4">
          <Button onClick={() => onOpenChange(false)} className={config.buttonClass}>
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Hook for easy usage
interface UseConfirmOptions {
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: ConfirmModalVariant;
}

export function useConfirm() {
  const [state, setState] = React.useState<{
    open: boolean;
    options: UseConfirmOptions;
    resolve: ((value: boolean) => void) | null;
  }>({
    open: false,
    options: { title: '' },
    resolve: null,
  });

  const confirm = React.useCallback((options: UseConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setState({ open: true, options, resolve });
    });
  }, []);

  const handleConfirm = React.useCallback(() => {
    state.resolve?.(true);
    setState((prev) => ({ ...prev, open: false, resolve: null }));
  }, [state.resolve]);

  const handleCancel = React.useCallback(() => {
    state.resolve?.(false);
    setState((prev) => ({ ...prev, open: false, resolve: null }));
  }, [state.resolve]);

  const handleOpenChange = React.useCallback((open: boolean) => {
    if (!open) {
      state.resolve?.(false);
      setState((prev) => ({ ...prev, open: false, resolve: null }));
    }
  }, [state.resolve]);

  const ConfirmDialog = React.useMemo(
    () => (
      <ConfirmModal
        open={state.open}
        onOpenChange={handleOpenChange}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
        {...state.options}
      />
    ),
    [state.open, state.options, handleOpenChange, handleConfirm, handleCancel]
  );

  return { confirm, ConfirmDialog };
}

// Hook for alert
interface UseAlertOptions {
  title: string;
  description?: string;
  confirmText?: string;
  variant?: ConfirmModalVariant;
}

export function useAlert() {
  const [state, setState] = React.useState<{
    open: boolean;
    options: UseAlertOptions;
  }>({
    open: false,
    options: { title: '' },
  });

  const alert = React.useCallback((options: UseAlertOptions) => {
    setState({ open: true, options });
  }, []);

  const handleOpenChange = React.useCallback((open: boolean) => {
    setState((prev) => ({ ...prev, open }));
  }, []);

  const AlertDialog = React.useMemo(
    () => (
      <AlertModal
        open={state.open}
        onOpenChange={handleOpenChange}
        {...state.options}
      />
    ),
    [state.open, state.options, handleOpenChange]
  );

  return { alert, AlertDialog };
}
