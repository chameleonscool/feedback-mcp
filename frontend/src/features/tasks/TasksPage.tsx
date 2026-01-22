import { useEffect, useRef, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch';
import {
  fetchPendingTasks,
  fetchHistory,
  selectTask,
  submitReply,
  dismissTask,
} from './tasksSlice';
import { fetchUserInfo, fetchFeishuNotifyStatus, updateFeishuNotify } from '@/features/user/userSlice';
import { clearAuth } from '@/features/auth/authSlice';
import { Button, Card } from '@/components/ui';
import { useNavigate } from 'react-router-dom';

export default function TasksPage() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const { pending, history, selectedTaskId, pollingStatus } = useAppSelector(
    (state) => state.tasks
  );
  const { profile, feishuNotifyEnabled } = useAppSelector((state) => state.user);

  const [replyText, setReplyText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const pollingRef = useRef<number | null>(null);

  const selectedTask = pending.find((t) => t.id === selectedTaskId);

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

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-80 bg-slate-800/50 border-r border-slate-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
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

        {/* Task List */}
        <div className="flex-1 overflow-y-auto p-2">
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
                      {new Date(task.createdAt).toLocaleString()}
                    </p>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-700 space-y-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleShowHistory}
            className="w-full"
          >
            📋 {showHistory ? '隐藏历史' : '查看历史'}
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

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {showHistory ? (
          <HistoryView history={history} onClose={() => setShowHistory(false)} />
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
          <EmptyState />
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
    <div className="flex-1 flex flex-col p-6">
      {/* Question */}
      <Card className="mb-6">
        <h3 className="text-sm font-medium text-slate-400 mb-2">📝 问题</h3>
        <p className="text-lg whitespace-pre-wrap">{task.question}</p>

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

      {/* Reply */}
      <Card className="flex-1 flex flex-col">
        <h3 className="text-sm font-medium text-slate-400 mb-2">💬 回复</h3>
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

        <div className="flex gap-3 mt-4">
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

interface HistoryViewProps {
  history: Array<{
    id: string;
    question: string;
    answer?: string;
    status: string;
    completedAt?: string;
  }>;
  onClose: () => void;
}

function HistoryView({ history, onClose }: HistoryViewProps) {
  return (
    <div className="flex-1 flex flex-col p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">📋 历史记录</h2>
        <Button variant="ghost" onClick={onClose}>
          ← 返回
        </Button>
      </div>

      {history.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-slate-500">
          <div className="text-center">
            <div className="text-6xl mb-4">📭</div>
            <p>暂无历史记录</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4 overflow-y-auto">
          {history.map((item) => (
            <Card key={item.id} padding="sm">
              <div className="flex items-start gap-4">
                <div
                  className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm
                  ${
                    item.status === 'COMPLETED'
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-slate-700 text-slate-400'
                  }
                `}
                >
                  {item.status === 'COMPLETED' ? '✓' : '—'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{item.question}</p>
                  {item.answer && (
                    <p className="text-slate-400 mt-1 text-sm">{item.answer}</p>
                  )}
                  {item.completedAt && (
                    <p className="text-xs text-slate-500 mt-2">
                      {new Date(item.completedAt).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <div className="text-8xl mb-4">🤖</div>
        <h2 className="text-2xl font-bold mb-2">AI Intent Center</h2>
        <p className="text-slate-400">选择左侧任务开始处理</p>
      </div>
    </div>
  );
}
