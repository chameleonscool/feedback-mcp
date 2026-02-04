import type { Task } from '@/types';
import type { TranslationKey } from '../i18n';

interface SidebarProps {
  profile: { name?: string; avatarUrl?: string } | null;
  pollingStatus: string;
  pending: Task[];
  history: Task[];
  selectedTaskId: string | null;
  selectedHistoryId: string | null;
  selectedHistoryIds: Set<string>;
  historyVisible: boolean;
  lang: 'en' | 'zh';
  notifyPermission: NotificationPermission;
  soundEnabled: boolean;
  feishuNotifyEnabled: boolean;
  t: (key: TranslationKey) => string;
  formatRelativeTime: (dateStr: string) => string;
  getNotifyStatusText: () => string;
  onToggleLang: () => void;
  onToggleSound: () => void;
  onToggleFeishuNotify: () => void;
  onSelectTask: (id: string) => void;
  onSelectHistoryItem: (id: string) => void;
  onToggleHistorySelection: (id: string, e: React.MouseEvent) => void;
  onToggleSelectAll: () => void;
  onDeleteSelected: () => void;
  onSetHistoryVisible: (visible: boolean) => void;
  onRequestNotificationPermission: () => void;
  onLogout: () => void;
}

export function Sidebar({
  profile,
  pollingStatus,
  pending,
  history,
  selectedTaskId,
  selectedHistoryId,
  selectedHistoryIds,
  historyVisible,
  lang,
  notifyPermission,
  soundEnabled,
  feishuNotifyEnabled,
  t,
  formatRelativeTime,
  getNotifyStatusText,
  onToggleLang,
  onToggleSound,
  onToggleFeishuNotify,
  onSelectTask,
  onSelectHistoryItem,
  onToggleHistorySelection,
  onToggleSelectAll,
  onDeleteSelected,
  onSetHistoryVisible,
  onRequestNotificationPermission,
  onLogout,
}: SidebarProps) {
  return (
    <aside className="w-80 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 flex flex-col shadow-2xl z-10">
      {/* 顶部用户信息区域 */}
      <div className="p-5 border-b border-slate-700/50 shrink-0">
        <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-2xl border border-slate-700/30 backdrop-blur">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center overflow-hidden shadow-lg shadow-violet-500/30 ring-2 ring-slate-700">
            {profile?.avatarUrl ? (
              <img
                src={profile.avatarUrl}
                alt=""
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-lg text-white font-bold">
                {(profile?.name || '用户').charAt(0).toUpperCase()}
              </span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-white truncate">
              {profile?.name || 'Loading...'}
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-xs text-emerald-400">{t('logged_in')}</span>
            </div>
          </div>
          <button
            onClick={onToggleLang}
            className="p-2 text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-all"
          >
            {lang === 'en' ? '中文' : 'English'}
          </button>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${pollingStatus === 'polling' || pollingStatus === 'idle' ? 'bg-emerald-400' : 'bg-red-400'}`}
              ></span>
              <span
                className={`relative inline-flex rounded-full h-2.5 w-2.5 ${pollingStatus === 'polling' || pollingStatus === 'idle' ? 'bg-emerald-500' : 'bg-red-500'}`}
              ></span>
            </span>
            <span className="text-xs text-slate-400 font-medium">
              {pollingStatus === 'error'
                ? t('status_disconnected')
                : t('status_connected')}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onToggleSound}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                ${
                  soundEnabled
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-slate-700/50 text-slate-400 border border-slate-600/30 hover:bg-slate-700'
                }
              `}
              title={soundEnabled ? t('sound_on') : t('sound_off')}
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {soundEnabled ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15.536 8.464a5 5 0 010 7.072M17.95 6.05a8 8 0 010 11.9M6.5 8.5l4-4v15l-4-4H3a1 1 0 01-1-1v-5a1 1 0 011-1h3.5z"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15zM17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
                  />
                )}
              </svg>
            </button>
            <button
              onClick={onToggleFeishuNotify}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                ${
                  feishuNotifyEnabled
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-slate-700/50 text-slate-400 border border-slate-600/30 hover:bg-slate-700'
                }
              `}
            >
              {feishuNotifyEnabled ? t('feishu_on') : t('feishu_off')}
            </button>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
          </div>
          <h1 className="text-lg font-bold text-white">{t('title')}</h1>
        </div>
      </div>

      {/* 任务列表区域 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <div className="flex items-center gap-2 px-1 mb-2">
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {t('pending_tasks')}
          </span>
        </div>

        <div className="space-y-2">
          {pending.length === 0 ? (
            <div className="text-center py-8 px-4">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-700/50 flex items-center justify-center">
                <span className="text-3xl">📭</span>
              </div>
              <p className="text-slate-500 text-sm font-medium">
                {t('no_tasks')}
              </p>
              <p className="text-slate-600 text-xs mt-1">{t('wait_ai')}</p>
            </div>
          ) : (
            pending.map((task) => (
              <button
                key={task.id}
                onClick={() => onSelectTask(task.id)}
                className={`
                  w-full text-left p-4 rounded-xl cursor-pointer transition-all duration-200 border-l-[3px]
                  ${
                    task.id === selectedTaskId
                      ? 'bg-gradient-to-r from-indigo-500/15 to-violet-500/10 border-l-violet-500'
                      : 'hover:bg-slate-700/30 border-l-transparent'
                  }
                `}
              >
                <div className="flex justify-between items-start mb-2">
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider ${task.id === selectedTaskId ? 'text-violet-400' : 'text-slate-500'}`}
                  >
                    {t('ticket')} #{task.id.substring(0, 6)}
                  </span>
                  <span
                    className={`text-[10px] ${task.id === selectedTaskId ? 'text-slate-400' : 'text-slate-600'}`}
                  >
                    {task.createdAt
                      ? formatRelativeTime(task.createdAt)
                      : t('just_now')}
                  </span>
                </div>
                <p
                  className={`text-sm font-medium line-clamp-2 leading-relaxed ${task.id === selectedTaskId ? 'text-white' : 'text-slate-400'}`}
                >
                  {task.question}
                </p>
              </button>
            ))
          )}
        </div>

        {/* 历史记录区域 */}
        {history.length > 0 && (
          <div className="mt-6 pt-4 border-t border-slate-700/50">
            <div className="flex items-center justify-between mb-3 px-1">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {t('history')}
              </span>
              <div className="flex items-center gap-2">
                {selectedHistoryIds.size > 0 && (
                  <>
                    <button
                      onClick={onToggleSelectAll}
                      className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
                    >
                      {selectedHistoryIds.size === history.length
                        ? t('deselect_all')
                        : t('select_all')}
                    </button>
                    <button
                      onClick={onDeleteSelected}
                      className="text-[10px] text-rose-400 hover:text-rose-300 transition-colors"
                    >
                      {t('delete_selected')} ({selectedHistoryIds.size})
                    </button>
                  </>
                )}
                <button
                  onClick={() => onSetHistoryVisible(!historyVisible)}
                  className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {historyVisible ? t('history_hide') : t('history_show')}
                </button>
              </div>
            </div>

            {historyVisible && (
              <div className="space-y-2">
                {history.map((item) => (
                  <div
                    key={item.id}
                    className={`
                      p-3 rounded-xl cursor-pointer transition-all duration-200 flex items-start gap-2 border-l-[3px]
                      ${
                        item.id === selectedHistoryId
                          ? 'bg-slate-700/50 border-l-green-500'
                          : 'hover:bg-slate-700/30 border-l-transparent text-slate-500 opacity-70'
                      }
                    `}
                  >
                    <input
                      type="checkbox"
                      checked={selectedHistoryIds.has(item.id)}
                      onClick={(e) => onToggleHistorySelection(item.id, e)}
                      onChange={() => {}}
                      className="mt-1 w-3 h-3 rounded border-slate-600 bg-slate-700 text-green-500 focus:ring-green-500 cursor-pointer shrink-0"
                    />
                    <div
                      onClick={() => onSelectHistoryItem(item.id)}
                      className="flex-1 min-w-0"
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-[10px] font-medium uppercase tracking-wider text-green-500">
                          ✓ {t('completed')}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {item.completedAt
                            ? formatRelativeTime(item.completedAt)
                            : ''}
                        </span>
                      </div>
                      <p className="text-xs line-clamp-2 leading-relaxed text-slate-400">
                        {item.question.substring(0, 80)}
                        {item.question.length > 80 ? '...' : ''}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 底部工具栏 */}
      <div className="p-4 border-t border-slate-700/50 bg-slate-900/50 shrink-0">
        <div className="flex items-center justify-between">
          <button
            onClick={onRequestNotificationPermission}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1.5"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
            <span
              className={
                notifyPermission === 'granted'
                  ? 'text-green-500 font-bold'
                  : notifyPermission === 'denied'
                    ? 'text-red-500 font-bold'
                    : ''
              }
            >
              {getNotifyStatusText()}
            </span>
          </button>
          <div className="text-[10px] text-slate-600">{t('sw_active')}</div>
        </div>

        <button
          onClick={onLogout}
          className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-xl transition-all"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
            />
          </svg>
          <span>{t('back_login')}</span>
        </button>
      </div>
    </aside>
  );
}
