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
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
  const [showHistory, setShowHistory] = useState(false);
  const [selectedHistoryIds, setSelectedHistoryIds] = useState<Set<string>>(new Set());
  const pollingRef = useRef<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const selectedTask = pending.find((t) => t.id === selectedTaskId);
  const selectedHistoryTask = history.find((t) => t.id === selectedHistoryId);

  useEffect(() => {
    // 加载用户信息
    dispatch(fetchUserInfo());
    dispatch(fetchFeishuNotifyStatus());

    // 开始轮询
    // 立即获取一次
    dispatch(fetchPendingTasks());

    // 每 3 秒轮询一次
    pollingRef.current = window.setInterval(() => {
      dispatch(fetchPendingTasks());
    }, 3000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
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
          if (file) {
            handleImageFile(file);
          }
        }
      }
    };

    document.addEventListener('paste', handlePaste);
    return () => document.removeEventListener('paste', handlePaste);
  }, []);


  const handleImageFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      setReplyImage(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleImageFile(file);
    }
  };

  const clearImage = () => {
    setReplyImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async () => {
    if (!selectedTaskId || (!replyText.trim() && !replyImage)) {
      alert('请输入内容或上传图片');
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
      alert('提交失败');
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
    // Ctrl+Enter 或 Cmd+Enter 发送
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleLogout = () => {
    dispatch(clearAuth());
    navigate('/login');
  };

  const handleShowHistory = () => {
    if (!showHistory) {
      dispatch(fetchHistory());
    }
    setShowHistory(!showHistory);
    // 切换时清除选择
    setSelectedHistoryIds(new Set());
  };

  // 历史记录多选
  const toggleHistorySelection = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newSet = new Set(selectedHistoryIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
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
      // 如果删除的包含当前选中的，清除选中
      if (selectedHistoryId && selectedHistoryIds.has(selectedHistoryId)) {
        dispatch(selectHistoryItem(null));
      }
      setSelectedHistoryIds(new Set());
    } catch (error) {
      console.error('删除失败:', error);
      alert('删除失败');
    }
  };

  // 格式化时间为相对时间
  const formatRelativeTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    const minutes = Math.floor(diff / (1000 * 60));
    if (minutes > 0) return `${minutes}分钟前`;
    return '刚刚';
  };

  return (
    <div className="h-screen flex overflow-hidden">
      {/* Sidebar - 独立滚动 */}
      <aside className="w-80 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 border-r border-slate-700/50 flex flex-col h-full overflow-hidden shadow-2xl">
        {/* Header - 固定 */}
        <div className="p-4 border-b border-slate-700/50 flex-shrink-0">
          {/* 用户信息卡片 */}
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
              <h2 className="font-semibold text-white truncate">{profile?.name || '用户'}</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="text-xs text-emerald-400">已登录</span>
              </div>
            </div>
          </div>
          
          {/* 状态指示器和飞书开关 */}
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${pollingStatus === 'polling' ? 'bg-emerald-400' : 'bg-slate-400'}`}></span>
                <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${pollingStatus === 'polling' ? 'bg-emerald-500' : 'bg-slate-500'}`}></span>
              </span>
              <span className="text-xs text-slate-400 font-medium">
                {pollingStatus === 'polling' ? '服务连接正常' : '连接中...'}
              </span>
            </div>
            
            {/* 飞书通知开关 */}
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
              {feishuNotifyEnabled ? '🔔 飞书 ON' : '🔕 飞书 OFF'}
            </button>
          </div>
          
          {/* 标题 */}
          <div className="mt-4 flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <span className="text-white text-sm">💬</span>
            </div>
            <h1 className="text-lg font-bold text-white">AI Intent</h1>
          </div>
        </div>

        {/* Task/History List - 可滚动 */}
        <div className="flex-1 overflow-y-auto p-3">
          {showHistory ? (
            // 历史列表
            <>
              <div className="flex items-center justify-between px-1 mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-400"></div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    历史记录 ({history.length})
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {selectedHistoryIds.size > 0 && (
                    <>
                      <button 
                        onClick={toggleSelectAll}
                        className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
                      >
                        {selectedHistoryIds.size === history.length ? '取消' : '全选'}
                      </button>
                      <button 
                        onClick={handleDeleteSelected}
                        className="text-[10px] text-rose-400 hover:text-rose-300 transition-colors"
                      >
                        删除 ({selectedHistoryIds.size})
                      </button>
                    </>
                  )}
                </div>
              </div>

              {history.length === 0 ? (
                <div className="text-center py-12 px-4">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-700/50 flex items-center justify-center">
                    <span className="text-3xl">📭</span>
                  </div>
                  <p className="text-slate-500 text-sm font-medium">暂无历史记录</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((item) => (
                    <div
                      key={item.id}
                      className={`
                        sidebar-item p-3 rounded-xl cursor-pointer transition-all duration-200 flex items-start gap-2
                        ${item.id === selectedHistoryId 
                          ? 'bg-gradient-to-r from-purple-500/15 to-violet-500/10 border-l-3 border-l-purple-500' 
                          : 'hover:bg-slate-700/30 border-l-3 border-l-transparent'
                        }
                      `}
                    >
                      <input 
                        type="checkbox" 
                        checked={selectedHistoryIds.has(item.id)}
                        onClick={(e) => toggleHistorySelection(item.id, e)}
                        onChange={() => {}}
                        className="mt-1 w-3.5 h-3.5 rounded border-slate-600 bg-slate-700 text-purple-500 focus:ring-purple-500 cursor-pointer flex-shrink-0"
                      />
                      <div 
                        onClick={() => dispatch(selectHistoryItem(item.id))}
                        className="flex-1 min-w-0"
                      >
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-[10px] font-medium uppercase tracking-wider text-green-500">
                            ✓ 已完成
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
            </>
          ) : (
            // 待处理任务列表
            <>
              <div className="flex items-center gap-2 px-1 mb-3">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  待处理任务 ({pending.length})
                </span>
              </div>

              {pending.length === 0 ? (
                <div className="text-center py-12 px-4">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-700/50 flex items-center justify-center">
                    <span className="text-3xl">📭</span>
                  </div>
                  <p className="text-slate-500 text-sm font-medium">暂无待处理任务</p>
                  <p className="text-slate-600 text-xs mt-1">请等待 AI 发起新的提问...</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {pending.map((task) => (
                    <button
                      key={task.id}
                      onClick={() => dispatch(selectTask(task.id))}
                      className={`
                        w-full text-left p-4 rounded-xl cursor-pointer transition-all duration-200
                        ${task.id === selectedTaskId 
                          ? 'bg-gradient-to-r from-blue-500/15 to-indigo-500/10 border-l-3 border-l-violet-500' 
                          : 'hover:bg-slate-700/30 border-l-3 border-l-transparent'
                        }
                      `}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${task.id === selectedTaskId ? 'text-violet-400' : 'text-slate-500'}`}>
                          任务 #{task.id.substring(0, 6)}
                        </span>
                        <span className={`text-[10px] ${task.id === selectedTaskId ? 'text-slate-400' : 'text-slate-600'}`}>
                          {task.createdAt ? formatRelativeTime(task.createdAt) : '刚刚'}
                        </span>
                      </div>
                      <p className={`text-sm font-medium line-clamp-2 leading-relaxed ${task.id === selectedTaskId ? 'text-white' : 'text-slate-400'}`}>
                        {task.question}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer - 固定 */}
        <div className="p-4 border-t border-slate-700/50 bg-slate-900/50 flex-shrink-0">
          <button
            onClick={handleShowHistory}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-xl transition-all mb-2"
          >
            📋 {showHistory ? '查看任务' : '查看历史'}
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-xl transition-all"
          >
            🚪 退出登录
          </button>
        </div>
      </aside>

      {/* Main Content - 独立滚动 */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-gradient-to-br from-slate-50 via-white to-blue-50/30 relative">
        {/* 装饰性背景 */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-violet-200/30 to-purple-200/30 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-blue-200/30 to-cyan-200/30 rounded-full blur-3xl"></div>
        </div>

        <div className="flex-1 overflow-y-auto p-8 relative z-0 flex items-start justify-center">
          {showHistory ? (
            selectedHistoryTask ? (
              <HistoryDetail item={selectedHistoryTask} />
            ) : (
              <EmptyState message="请从左侧列表选择一个历史记录" icon="📋" />
            )
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
              textareaRef={textareaRef}
            />
          ) : (
            <EmptyState message="请从左侧列表选择一个任务进行回复" icon="🤖" />
          )}
        </div>

        {/* 隐藏的文件输入 */}
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
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}

function TaskDetail({
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
  textareaRef,
}: TaskDetailProps) {
  return (
    <div className="w-full max-w-2xl animate-fade-in">
      <div className="glass rounded-2xl shadow-xl overflow-hidden">
        {/* Question */}
        <div className="bg-gray-50/50 border-b border-gray-100 p-6">
          <div className="flex items-center space-x-2 mb-3">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-600 uppercase tracking-wide">
              处理中
            </span>
            <span className="text-xs text-gray-400 font-mono">ID: {task.id.substring(0, 8)}</span>
          </div>
          <div className="markdown-content text-gray-800 prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{task.question}</ReactMarkdown>
          </div>

          {task.image && (
            <div className="mt-4">
              <img
                src={task.image}
                alt="附图"
                className="max-w-full rounded-lg border border-gray-200 shadow-sm"
              />
            </div>
          )}
        </div>

        {/* Reply Form */}
        <div className="p-6 space-y-6 bg-white/60">
          {/* Textarea */}
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="请输入您的回复... (Ctrl+Enter 发送)"
              className="
                w-full h-40 p-4 
                bg-white border border-gray-200 rounded-xl 
                focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                outline-none transition-all resize-none 
                text-gray-700 placeholder-gray-400 text-base leading-relaxed 
                shadow-sm hover:border-gray-300
              "
              autoFocus
            />
            <div className="absolute bottom-3 right-3 text-xs text-gray-400 pointer-events-none bg-white/80 px-2 py-1 rounded">
              支持 Markdown | ⌘+Enter
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
                  <img 
                    src={replyImage} 
                    alt="预览" 
                    className="max-h-64 rounded-lg shadow-md border border-gray-200"
                  />
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
                  <p className="text-sm text-gray-500 font-medium group-hover:text-blue-600 transition-colors">
                    点击上传截图
                  </p>
                  <p className="text-xs text-gray-400 mt-1">或直接粘贴图片到页面</p>
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
              忽略 (Dismiss)
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
                  <span>发送回复</span>
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

interface HistoryItemType {
  id: string;
  question: string;
  answer?: string;
  status: string;
  completedAt?: string;
}

interface HistoryDetailProps {
  item: HistoryItemType;
}

function HistoryDetail({ item }: HistoryDetailProps) {
  return (
    <div className="w-full max-w-2xl animate-fade-in">
      <div className="glass rounded-2xl shadow-xl overflow-hidden">
        {/* Question */}
        <div className="bg-green-50/50 border-b border-green-100 p-6">
          <div className="flex items-center space-x-2 mb-3">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-600 uppercase tracking-wide">
              ✓ 已完成
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
          <h3 className="text-sm font-semibold text-gray-500 mb-2">Your Reply:</h3>
          {item.answer ? (
            <div className="bg-gray-50 rounded-lg p-4 text-gray-700 prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.answer}</ReactMarkdown>
            </div>
          ) : (
            <p className="text-gray-400 italic">(No reply)</p>
          )}
        </div>
      </div>
    </div>
  );
}

interface EmptyStateProps {
  message: string;
  icon: string;
}

function EmptyState({ message, icon }: EmptyStateProps) {
  return (
    <div className="text-center text-gray-400 animate-fade-in">
      <div className="w-24 h-24 mx-auto mb-6 bg-gray-50 rounded-full flex items-center justify-center">
        <span className="text-4xl opacity-30">{icon}</span>
      </div>
      <p className="text-xl font-medium text-gray-500">AI Intent Center</p>
      <p className="text-sm mt-2 opacity-60">{message}</p>
    </div>
  );
}
