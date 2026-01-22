import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { TranslationKey } from '../i18n';

interface TaskDetailProps {
  task: { id: string; question: string; image?: string };
  replyText: string;
  setReplyText: (text: string) => void;
  replyImage: string | null;
  onImageSelect: () => void;
  onClearImage: () => void;
  onSubmit: () => void;
  onDismiss: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  submitting: boolean;
  t: (key: TranslationKey) => string;
}

export function TaskDetail({
  task,
  replyText,
  setReplyText,
  replyImage,
  onImageSelect,
  onClearImage,
  onSubmit,
  onDismiss,
  onKeyDown,
  submitting,
  t,
}: TaskDetailProps) {
  return (
    <div className="w-full min-w-[32rem] animate-fade-in">
      <div className="glass rounded-2xl shadow-xl overflow-hidden">
        {/* Question */}
        <div className="bg-gray-50/50 border-b border-gray-100 p-6">
          <div className="flex items-center space-x-2 mb-3">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-600 uppercase tracking-wide">
              {t('status_pending')}
            </span>
            <span className="text-xs text-gray-400 font-mono">ID: {task.id.substring(0, 8)}</span>
          </div>
          <div className="markdown-content text-gray-800 prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{task.question}</ReactMarkdown>
          </div>

          {task.image && (
            <div className="mt-4">
              <img src={task.image} alt="附图" className="max-w-full rounded-lg border border-gray-200 shadow-sm" />
            </div>
          )}
        </div>

        {/* Reply Form */}
        <div className="p-6 space-y-6 bg-white/60">
          <div className="relative">
            <textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={t('placeholder')}
              className="w-full h-40 p-4 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all resize-none text-gray-700 placeholder-gray-400 text-base leading-relaxed shadow-sm hover:border-gray-300"
              autoFocus
            />
            <div className="absolute bottom-3 right-3 text-xs text-gray-400 pointer-events-none bg-white/80 px-2 py-1 rounded">
              {t('markdown_tip')}
            </div>
          </div>

          {/* Image Upload */}
          <div className="relative group">
            <div 
              onClick={onImageSelect}
              className="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center transition-all duration-200 hover:bg-blue-50/30 hover:border-blue-300 cursor-pointer"
            >
              {replyImage ? (
                <div className="relative inline-block">
                  <img src={replyImage} alt="预览" className="max-h-64 rounded-lg shadow-md border border-gray-200" />
                  <button 
                    onClick={(e) => { e.stopPropagation(); onClearImage(); }}
                    className="absolute -top-3 -right-3 bg-white text-red-500 rounded-full p-1.5 shadow-md hover:bg-red-50 border border-gray-100 transition-all transform hover:scale-110"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ) : (
                <>
                  <svg className="w-10 h-10 mx-auto text-gray-300 group-hover:text-blue-500 transition-colors mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p className="text-sm text-gray-500 font-medium group-hover:text-blue-600 transition-colors">{t('upload_img')}</p>
                  <p className="text-xs text-gray-400 mt-1">{t('paste_tip')}</p>
                </>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-4 pt-4 border-t border-gray-100">
            <button 
              onClick={onDismiss}
              className="px-6 py-3 text-gray-500 hover:text-red-600 hover:bg-red-50 font-medium rounded-xl transition-all duration-200 text-sm"
            >
              {t('dismiss')}
            </button>
            <button 
              onClick={onSubmit}
              disabled={submitting}
              className="flex-1 px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/30 transition-all duration-200 transform hover:-translate-y-0.5 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 flex justify-center items-center gap-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {submitting ? (
                <span className="animate-spin">⏳</span>
              ) : (
                <>
                  <span>{t('send')}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
