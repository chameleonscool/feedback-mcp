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
import { TaskDetail, HistoryDetail, EmptyState, Sidebar } from './components';
import { useNotificationSound, useNewTaskNotification } from './hooks/useNotificationSound';

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

  // 提示音 hook
  const { soundEnabled, toggleSound, playNotificationSound } = useNotificationSound();
  
  // 新任务提示音
  useNewTaskNotification(
    pending.map(t => t.id),
    playNotificationSound
  );

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

  const handleSelectTask = (id: string) => {
    dispatch(selectTask(id));
    dispatch(selectHistoryItem(null));
  };

  const handleSelectHistoryItem = (id: string) => {
    dispatch(selectHistoryItem(id));
    dispatch(selectTask(null));
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
      <Sidebar
        profile={profile}
        pollingStatus={pollingStatus}
        pending={pending}
        history={history}
        selectedTaskId={selectedTaskId}
        selectedHistoryId={selectedHistoryId}
        selectedHistoryIds={selectedHistoryIds}
        historyVisible={historyVisible}
        lang={lang}
        notifyPermission={notifyPermission}
        soundEnabled={soundEnabled}
        feishuNotifyEnabled={feishuNotifyEnabled}
        t={t}
        formatRelativeTime={formatRelativeTime}
        getNotifyStatusText={getNotifyStatusText}
        onToggleLang={toggleLang}
        onToggleSound={toggleSound}
        onToggleFeishuNotify={() => dispatch(updateFeishuNotify(!feishuNotifyEnabled))}
        onSelectTask={handleSelectTask}
        onSelectHistoryItem={handleSelectHistoryItem}
        onToggleHistorySelection={toggleHistorySelection}
        onToggleSelectAll={toggleSelectAll}
        onDeleteSelected={handleDeleteSelected}
        onSetHistoryVisible={setHistoryVisible}
        onRequestNotificationPermission={requestNotificationPermission}
        onLogout={handleLogout}
      />

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
