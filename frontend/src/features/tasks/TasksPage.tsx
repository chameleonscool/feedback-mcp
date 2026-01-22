import { useEffect, useRef, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch';
import {
  fetchPendingTasks,
  fetchHistory,
  selectTask,
  submitReply,
  dismissTask,
  selectHistoryItem,
  deleteHistory,
} from './tasksSlice';
import { fetchUserInfo, fetchFeishuNotifyStatus, updateFeishuNotify } from '@/features/user/userSlice';
import { clearAuth } from '@/features/auth/authSlice';
import { useNavigate } from 'react-router-dom';

import { translations, type Lang, type TranslationKey } from './i18n';
import { TaskDetail, HistoryDetail, EmptyState } from './components';

export default function TasksPage() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const { pending, history, selectedTaskId, selectedHistoryId, pollingStatus } = useAppSelector(
    (state) => state.tasks
  );
  const { profile, feishuNotifyEnabled } = useAppSelector((state) => state.user);

  const [replyText, setReplyText] = useState('');
  const [replyImage, setReplyImage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [historyVisible, setHistoryVisible] = useState(true);
  const [selectedHistoryIds, setSelectedHistoryIds] = useState<Set<string>>(new Set());
  const [lang, setLang] = useState<Lang>(() => (localStorage.getItem('lang') as Lang) || 'en');
  const [notifyPermission, setNotifyPermission] = useState<NotificationPermission>('default');
  
  const pollingRef = useRef<number | null>(null);
  const historyPollingRef = useRef<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const selectedTask = pending.find((t) => t.id === selectedTaskId);
  const selectedHistoryTask = history.find((t) => t.id === selectedHistoryId);

  // 翻译函数
  const t = (key: TranslationKey): string => translations[lang][key];

  useEffect(() => {
    dispatch(fetchUserInfo());
    dispatch(fetchFeishuNotifyStatus());

    if ('Notification' in window) {
      setNotifyPermission(Notification.permission);
    }

    dispatch(fetchPendingTasks());
    pollingRef.current = window.setInterval(() => {
      dispatch(fetchPendingTasks());
    }, 1500);

    dispatch(fetchHistory());
    historyPollingRef.current = window.setInterval(() => {
      dispatch(fetchHistory());
    }, 5000);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
      if (historyPollingRef.current) clearInterval(historyPollingRef.current);
    };
  }, [dispatch]);

  // 粘贴图片处理
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) handleImageFile(file);
        }
      }
    };

    document.addEventListener('paste', handlePaste);
    return () => document.removeEventListener('paste', handlePaste);
  }, []);

  const toggleLang = () => {
    const newLang = lang === 'en' ? 'zh' : 'en';
    setLang(newLang);
    localStorage.setItem('lang', newLang);
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setNotifyPermission(permission);
      if (permission === 'granted') {
        new Notification(t('title'), { body: t('notify_granted') });
      }
    }
  };

  const handleImageFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => setReplyImage(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleImageFile(file);
  };

  const clearImage = () => {
    setReplyImage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async () => {
    if (!selectedTaskId || (!replyText.trim() && !replyImage)) {
      alert(t('alert_empty'));
      return;
    }

    setSubmitting(true);
    try {
      await dispatch(submitReply({ 
        id: selectedTaskId, 
        answer: replyText,
        image: replyImage || undefined
      })).unwrap();
      setReplyText('');
      setReplyImage(null);
    } catch (error) {
      console.error('提交失败:', error);
      alert(t('alert_fail'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDismiss = async () => {
    if (!selectedTaskId) return;
    try {
      await dispatch(dismissTask(selectedTaskId)).unwrap();
    } catch (error) {
      console.error('忽略失败:', error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleLogout = () => {
    dispatch(clearAuth());
    navigate('/login');
  };

  const toggleHistorySelection = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newSet = new Set(selectedHistoryIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedHistoryIds(newSet);
  };

  const toggleSelectAll = () => {
    if (selectedHistoryIds.size === history.length) {
      setSelectedHistoryIds(new Set());
    } else {
      setSelectedHistoryIds(new Set(history.map(h => h.id)));
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedHistoryIds.size === 0) return;
    try {
      await dispatch(deleteHistory(Array.from(selectedHistoryIds))).unwrap();
      if (selectedHistoryId && selectedHistoryIds.has(selectedHistoryId)) {
        dispatch(selectHistoryItem(null));
      }
      setSelectedHistoryIds(new Set());
    } catch (error) {
      console.error('删除失败:', error);
    }
  };

  const formatRelativeTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (mins < 1) return t('just_now');
    if (mins < 60) return `${mins}m`;
    if (hours < 24) return `${hours}h`;
    return `${days}d`;
  };

  const getNotifyStatusText = () => {
    if (notifyPermission === 'granted') return t('notify_granted');
    if (notifyPermission === 'denied') return t('notify_denied');
    return t('notify_default');
  };

  return (
    <div className="h-screen flex overflow-hidden">
      {/* Sidebar */}
      <aside className="w-80 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 flex flex-col shadow-2xl z-10">
        {/* 顶部用户信息区域 */}
        <div className="p-5 border-b border-slate-700/50 shrink-0">
          <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-2xl border border-slate-700/30 backdrop-blur">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center overflow-hidden shadow-lg shadow-violet-500/30 ring-2 ring-slate-700">
              {profile?.avatarUrl ? (
                <img src={profile.avatarUrl} alt="" className="w-full h-full object-cover" />
              ) : (
                <span className="text-lg text-white font-bold">
                  {(profile?.name || '用户').charAt(0).toUpperCase()}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-white truncate">{profile?.name || 'Loading...'}</div>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="text-xs text-emerald-400">{t('logged_in')}</span>
              </div>
            </div>
            <button
              onClick={toggleLang}
              className="p-2 text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-all"
            >
              {lang === 'en' ? '中文' : 'English'}
            </button>
          </div>
          
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${pollingStatus === 'polling' || pollingStatus === 'idle' ? 'bg-emerald-400' : 'bg-red-400'}`}></span>
                <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${pollingStatus === 'polling' || pollingStatus === 'idle' ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
              </span>
              <span className="text-xs text-slate-400 font-medium">
                {pollingStatus === 'error' ? t('status_disconnected') : t('status_connected')}
              </span>
            </div>
            
            <button
              onClick={() => dispatch(updateFeishuNotify(!feishuNotifyEnabled))}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                ${feishuNotifyEnabled 
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                  : 'bg-slate-700/50 text-slate-400 border border-slate-600/30 hover:bg-slate-700'
                }
              `}
            >
              {feishuNotifyEnabled ? t('feishu_on') : t('feishu_off')}
            </button>
          </div>
          
          <div className="mt-4 flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
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
                <p className="text-slate-500 text-sm font-medium">{t('no_tasks')}</p>
                <p className="text-slate-600 text-xs mt-1">{t('wait_ai')}</p>
              </div>
            ) : (
              pending.map((task) => (
                <button
                  key={task.id}
                  onClick={() => {
                    dispatch(selectTask(task.id));
                    dispatch(selectHistoryItem(null));
                  }}
                  className={`
                    w-full text-left p-4 rounded-xl cursor-pointer transition-all duration-200 border-l-[3px]
                    ${task.id === selectedTaskId 
                      ? 'bg-gradient-to-r from-indigo-500/15 to-violet-500/10 border-l-violet-500' 
                      : 'hover:bg-slate-700/30 border-l-transparent'
                    }
                  `}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${task.id === selectedTaskId ? 'text-violet-400' : 'text-slate-500'}`}>
                      {t('ticket')} #{task.id.substring(0, 6)}
                    </span>
                    <span className={`text-[10px] ${task.id === selectedTaskId ? 'text-slate-400' : 'text-slate-600'}`}>
                      {task.createdAt ? formatRelativeTime(task.createdAt) : t('just_now')}
                    </span>
                  </div>
                  <p className={`text-sm font-medium line-clamp-2 leading-relaxed ${task.id === selectedTaskId ? 'text-white' : 'text-slate-400'}`}>
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
                      <button onClick={toggleSelectAll} className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors">
                        {selectedHistoryIds.size === history.length ? t('deselect_all') : t('select_all')}
                      </button>
                      <button onClick={handleDeleteSelected} className="text-[10px] text-rose-400 hover:text-rose-300 transition-colors">
                        {t('delete_selected')} ({selectedHistoryIds.size})
                      </button>
                    </>
                  )}
                  <button 
                    onClick={() => setHistoryVisible(!historyVisible)} 
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
                        ${item.id === selectedHistoryId 
                          ? 'bg-slate-700/50 border-l-green-500' 
                          : 'hover:bg-slate-700/30 border-l-transparent text-slate-500 opacity-70'
                        }
                      `}
                    >
                      <input 
                        type="checkbox" 
                        checked={selectedHistoryIds.has(item.id)}
                        onClick={(e) => toggleHistorySelection(item.id, e)}
                        onChange={() => {}}
                        className="mt-1 w-3 h-3 rounded border-slate-600 bg-slate-700 text-green-500 focus:ring-green-500 cursor-pointer shrink-0"
                      />
                      <div 
                        onClick={() => {
                          dispatch(selectHistoryItem(item.id));
                          dispatch(selectTask(null));
                        }}
                        className="flex-1 min-w-0"
                      >
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-[10px] font-medium uppercase tracking-wider text-green-500">
                            ✓ {t('completed')}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {item.completedAt ? formatRelativeTime(item.completedAt) : ''}
                          </span>
                        </div>
                        <p className="text-xs line-clamp-2 leading-relaxed text-slate-400">
                          {item.question.substring(0, 80)}{item.question.length > 80 ? '...' : ''}
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
              onClick={requestNotificationPermission}
              className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1.5"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span className={notifyPermission === 'granted' ? 'text-green-500 font-bold' : notifyPermission === 'denied' ? 'text-red-500 font-bold' : ''}>
                {getNotifyStatusText()}
              </span>
            </button>
            <div className="text-[10px] text-slate-600">
              {t('sw_active')}
            </div>
          </div>
          
          <button
            onClick={handleLogout}
            className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-xl transition-all"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
            <span>{t('back_login')}</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-violet-200/30 to-purple-200/30 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-blue-200/30 to-cyan-200/30 rounded-full blur-3xl"></div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 lg:p-8 relative z-0">
          {selectedHistoryTask ? (
            <HistoryDetail item={selectedHistoryTask} t={t} />
          ) : selectedTask ? (
            <TaskDetail
              task={selectedTask}
              replyText={replyText}
              setReplyText={setReplyText}
              replyImage={replyImage}
              onImageSelect={() => fileInputRef.current?.click()}
              onClearImage={clearImage}
              onSubmit={handleSubmit}
              onDismiss={handleDismiss}
              onKeyDown={handleKeyDown}
              submitting={submitting}
              t={t}
            />
          ) : (
            <EmptyState t={t} />
          )}
        </div>

        <input
          type="file"
          ref={fileInputRef}
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
        />
      </main>
    </div>
  );
}
