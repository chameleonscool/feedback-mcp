import { useEffect, useRef, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch';
import {
  fetchPendingTasks,
  fetchHistory,
  selectTask,
  submitReply,
  dismissTask,
  selectHistoryItem,
} from './tasksSlice';
import { fetchUserInfo, fetchFeishuNotifyStatus, updateFeishuNotify } from '@/features/user/userSlice';
import { clearAuth } from '@/features/auth/authSlice';
import { Button, Card } from '@/components/ui';
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
  const [submitting, setSubmitting] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const pollingRef = useRef<number | null>(null);

  const selectedTask = pending.find((t) => t.id === selectedTaskId);
  const selectedHistoryTask = history.find((t) => t.id === selectedHistoryId);

  useEffect(() => {
    // 加载用户信息
    dispatch(fetchUserInfo());
    dispatch(fetchFeishuNotifyStatus());

    // 开始轮询
    startPolling();

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [dispatch]);

  const startPolling = () => {
    // 立即获取一次
    dispatch(fetchPendingTasks());

    // 每 3 秒轮询一次
    pollingRef.current = window.setInterval(() => {
      dispatch(fetchPendingTasks());
    }, 3000);
  };

  const handleSubmit = async () => {
    if (!selectedTaskId || !replyText.trim()) return;

    setSubmitting(true);
    try {
      await dispatch(submitReply({ id: selectedTaskId, answer: replyText })).unwrap();
      setReplyText('');
    } catch (error) {
      console.error('提交失败:', error);
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

  const handleLogout = () => {
    dispatch(clearAuth());
    navigate('/login');
  };

  const handleShowHistory = () => {
    if (!showHistory) {
      dispatch(fetchHistory());
    }
    setShowHistory(!showHistory);
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
      <aside className="w-80 bg-slate-800/50 border-r border-slate-700 flex flex-col h-full overflow-hidden">
        {/* Header - 固定 */}
        <div className="p-4 border-b border-slate-700 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center overflow-hidden">
              {profile?.avatarUrl ? (
                <img
                  src={profile.avatarUrl}
                  alt=""
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                <span className="text-lg">👤</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="font-semibold truncate">{profile?.name || '用户'}</h2>
              <button
                onClick={() => dispatch(updateFeishuNotify(!feishuNotifyEnabled))}
                className={`
                  text-xs px-2 py-1 rounded-lg mt-1 transition-all
                  ${feishuNotifyEnabled 
                    ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                    : 'bg-slate-700/50 text-slate-400 border border-slate-600/30 hover:bg-slate-700'
                  }
                `}
              >
                {feishuNotifyEnabled ? '🔔 飞书通知 ON' : '🔕 飞书通知 OFF'}
              </button>
            </div>
          </div>
        </div>

        {/* Task/History List - 可滚动 */}
        <div className="flex-1 overflow-y-auto p-2">
          {showHistory ? (
            // 历史列表
            <>
              <div className="flex items-center justify-between px-2 mb-2">
                <span className="text-sm text-slate-400">
                  历史记录 ({history.length})
                </span>
              </div>

              {history.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <div className="text-4xl mb-2">📭</div>
                  <p>暂无历史记录</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {history.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => dispatch(selectHistoryItem(item.id))}
                      className={`
                        w-full text-left p-3 rounded-xl transition-all
                        ${
                          item.id === selectedHistoryId
                            ? 'bg-purple-500/20 border border-purple-500/30'
                            : 'hover:bg-slate-700/50'
                        }
                      `}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`
                          w-5 h-5 rounded-full flex items-center justify-center text-xs
                          ${item.status === 'COMPLETED' 
                            ? 'bg-green-500/20 text-green-400' 
                            : 'bg-slate-700 text-slate-400'
                          }
                        `}>
                          {item.status === 'COMPLETED' ? '✓' : '—'}
                        </span>
                        <span className="text-xs text-slate-500">
                          {item.completedAt ? formatRelativeTime(item.completedAt) : ''}
                        </span>
                      </div>
                      <p className="text-sm line-clamp-2 text-slate-300">{item.question}</p>
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            // 待处理任务列表
            <>
              <div className="flex items-center justify-between px-2 mb-2">
                <span className="text-sm text-slate-400">
                  待处理任务 ({pending.length})
                </span>
                <div
                  className={`w-2 h-2 rounded-full ${
                    pollingStatus === 'polling' ? 'bg-green-500 animate-pulse' : 'bg-slate-500'
                  }`}
                />
              </div>

              {pending.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <div className="text-4xl mb-2">📭</div>
                  <p>暂无待处理任务</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {pending.map((task) => (
                    <button
                      key={task.id}
                      onClick={() => dispatch(selectTask(task.id))}
                      className={`
                        w-full text-left p-3 rounded-xl transition-all
                        ${
                          task.id === selectedTaskId
                            ? 'bg-blue-500/20 border border-blue-500/30'
                            : 'hover:bg-slate-700/50'
                        }
                      `}
                    >
                      <p className="text-sm line-clamp-2">{task.question}</p>
                      {task.createdAt && (
                        <p className="text-xs text-slate-500 mt-1">
                          {formatRelativeTime(task.createdAt)}
                        </p>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer - 固定 */}
        <div className="p-4 border-t border-slate-700 space-y-2 flex-shrink-0">
          <Button
            variant={showHistory ? 'primary' : 'secondary'}
            size="sm"
            onClick={handleShowHistory}
            className="w-full"
          >
            📋 {showHistory ? '查看任务' : '查看历史'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="w-full"
          >
            🚪 退出登录
          </Button>
        </div>
      </aside>

      {/* Main Content - 独立滚动 */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {showHistory ? (
          selectedHistoryTask ? (
            <HistoryDetail item={selectedHistoryTask} />
          ) : (
            <EmptyState message="选择左侧历史记录查看详情" icon="📋" />
          )
        ) : selectedTask ? (
          <TaskDetail
            task={selectedTask}
            replyText={replyText}
            setReplyText={setReplyText}
            onSubmit={handleSubmit}
            onDismiss={handleDismiss}
            submitting={submitting}
          />
        ) : (
          <EmptyState message="选择左侧任务开始处理" icon="🤖" />
        )}
      </main>
    </div>
  );
}

interface TaskDetailProps {
  task: { id: string; question: string; image?: string };
  replyText: string;
  setReplyText: (text: string) => void;
  onSubmit: () => void;
  onDismiss: () => void;
  submitting: boolean;
}

function TaskDetail({
  task,
  replyText,
  setReplyText,
  onSubmit,
  onDismiss,
  submitting,
}: TaskDetailProps) {
  return (
    <div className="flex-1 flex flex-col p-6 overflow-hidden">
      {/* Question - 可滚动 */}
      <Card className="mb-6 overflow-y-auto max-h-[50%]">
        <h3 className="text-sm font-medium text-slate-400 mb-2">📝 问题</h3>
        <div className="prose prose-invert prose-sm max-w-none prose-table:border prose-table:border-slate-600 prose-th:bg-slate-700 prose-th:p-2 prose-td:p-2 prose-td:border prose-td:border-slate-600">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{task.question}</ReactMarkdown>
        </div>

        {task.image && (
          <div className="mt-4">
            <img
              src={task.image}
              alt="附图"
              className="max-w-full rounded-lg border border-slate-700"
            />
          </div>
        )}
      </Card>

      {/* Reply - 固定高度 */}
      <Card className="flex-1 flex flex-col min-h-0">
        <h3 className="text-sm font-medium text-slate-400 mb-2 flex-shrink-0">💬 回复</h3>
        <textarea
          value={replyText}
          onChange={(e) => setReplyText(e.target.value)}
          placeholder="输入你的回复..."
          className="
            flex-1 w-full resize-none
            bg-slate-900 border border-slate-700 rounded-xl
            p-4 text-white placeholder-slate-500
            focus:outline-none focus:ring-2 focus:ring-blue-500
          "
        />

        <div className="flex gap-3 mt-4 flex-shrink-0">
          <Button onClick={onSubmit} loading={submitting} className="flex-1">
            ✅ 提交回复
          </Button>
          <Button variant="danger" onClick={onDismiss}>
            ❌ 忽略
          </Button>
        </div>
      </Card>
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
    <div className="flex-1 flex flex-col p-6 overflow-hidden">
      {/* Question */}
      <Card className="mb-6 overflow-y-auto max-h-[40%]">
        <div className="flex items-center gap-2 mb-2">
          <span className={`
            w-6 h-6 rounded-full flex items-center justify-center text-xs
            ${item.status === 'COMPLETED' 
              ? 'bg-green-500/20 text-green-400' 
              : 'bg-slate-700 text-slate-400'
            }
          `}>
            {item.status === 'COMPLETED' ? '✓' : '—'}
          </span>
          <h3 className="text-sm font-medium text-slate-400">📝 问题</h3>
          {item.completedAt && (
            <span className="text-xs text-slate-500 ml-auto">
              {new Date(item.completedAt).toLocaleString()}
            </span>
          )}
        </div>
        <div className="prose prose-invert prose-sm max-w-none prose-table:border prose-table:border-slate-600 prose-th:bg-slate-700 prose-th:p-2 prose-td:p-2 prose-td:border prose-td:border-slate-600">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.question}</ReactMarkdown>
        </div>
      </Card>

      {/* Answer */}
      <Card className="flex-1 overflow-y-auto">
        <h3 className="text-sm font-medium text-slate-400 mb-2">💬 回复</h3>
        {item.answer ? (
          <div className="prose prose-invert prose-sm max-w-none prose-table:border prose-table:border-slate-600 prose-th:bg-slate-700 prose-th:p-2 prose-td:p-2 prose-td:border prose-td:border-slate-600">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.answer}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-slate-500 italic">无回复</p>
        )}
      </Card>
    </div>
  );
}

interface EmptyStateProps {
  message: string;
  icon: string;
}

function EmptyState({ message, icon }: EmptyStateProps) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <div className="text-8xl mb-4">{icon}</div>
        <h2 className="text-2xl font-bold mb-2">AI Intent Center</h2>
        <p className="text-slate-400">{message}</p>
      </div>
    </div>
  );
}
