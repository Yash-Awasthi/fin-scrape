import { useTranslation } from 'react-i18next'

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

const SIZES = { sm: 'h-5 w-5', md: 'h-8 w-8', lg: 'h-12 w-12' };

export default function LoadingSpinner({ message, size = 'md' }: LoadingSpinnerProps) {
  const { t } = useTranslation()
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <svg
        className={`animate-spin text-brand-500 ${SIZES[size]}`}
        viewBox="0 0 24 24"
        fill="none"
        role="status"
        aria-label={message || t('common.loading')}
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      {message && <p className="text-sm text-surface-500">{message}</p>}
    </div>
  );
}
