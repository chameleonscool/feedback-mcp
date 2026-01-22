import type { TranslationKey } from '../i18n';

interface EmptyStateProps {
  t: (key: TranslationKey) => string;
}

export function EmptyState({ t }: EmptyStateProps) {
  return (
    <div className="w-full min-w-[32rem] flex flex-col items-center justify-center py-20 text-gray-400 animate-fade-in">
      <div className="w-24 h-24 mx-auto mb-6 bg-gray-50 rounded-full flex items-center justify-center">
        <svg className="w-10 h-10 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
      </div>
      <p className="text-xl font-medium text-gray-500">{t('all_done')}</p>
      <p className="text-sm mt-2 opacity-60">{t('select_task_tip')}</p>
    </div>
  );
}
