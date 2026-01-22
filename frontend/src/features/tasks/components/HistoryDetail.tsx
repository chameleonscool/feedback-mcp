import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { TranslationKey } from '../i18n';

interface HistoryDetailProps {
  item: { id: string; question: string; answer?: string; completedAt?: string };
  t: (key: TranslationKey) => string;
}

export function HistoryDetail({ item, t }: HistoryDetailProps) {
  return (
    <div className="w-full min-w-[32rem] animate-fade-in">
      <div className="glass rounded-2xl shadow-xl overflow-hidden">
        {/* Question */}
        <div className="bg-green-50/50 border-b border-green-100 p-6">
          <div className="flex items-center space-x-2 mb-3">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-600 uppercase tracking-wide">
              ✓ {t('completed')}
            </span>
            <span className="text-xs text-gray-400 font-mono">ID: {item.id.substring(0, 8)}</span>
            {item.completedAt && (
              <span className="text-xs text-gray-400 ml-auto">
                {new Date(item.completedAt).toLocaleString()}
              </span>
            )}
          </div>
          <div className="markdown-content text-gray-800 prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.question}</ReactMarkdown>
          </div>
        </div>

        {/* Answer */}
        <div className="p-6 bg-white/60">
          <h3 className="text-sm font-semibold text-gray-500 mb-2">{t('your_reply')}</h3>
          {item.answer ? (
            <div className="bg-gray-50 rounded-lg p-4 text-gray-700 prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.answer}</ReactMarkdown>
            </div>
          ) : (
            <p className="text-gray-400 italic">{t('no_reply')}</p>
          )}
        </div>
      </div>
    </div>
  );
}
