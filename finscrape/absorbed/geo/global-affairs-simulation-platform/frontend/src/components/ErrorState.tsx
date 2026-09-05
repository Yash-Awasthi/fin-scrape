import { useTranslation } from 'react-i18next'

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ title, message, onRetry }: ErrorStateProps) {
  const { t } = useTranslation()
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 px-4" role="alert">
      <span className="text-3xl" aria-hidden="true">&#9888;&#65039;</span>
      <h3 className="text-lg font-semibold text-surface-200">{title ?? t('common.error')}</h3>
      <p className="text-sm text-surface-500 text-center max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 px-4 py-2 text-sm bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors"
        >
          {t('common.retry')}
        </button>
      )}
    </div>
  );
}
