import { useEffect, useState } from 'react';
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch';
import { adminLogout, fetchAdminUsers, verifyAdminSession } from './adminSlice';
import { Button, Card, CardTitle, Input } from '@/components/ui';
import { adminApi } from '@/services/api';

export default function AdminDashboard() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { users, stats } = useAppSelector((state) => state.admin);

  useEffect(() => {
    dispatch(verifyAdminSession())
      .unwrap()
      .catch(() => {
        navigate('/admin/login');
      });

    dispatch(fetchAdminUsers());
  }, [dispatch, navigate]);

  const handleLogout = async () => {
    await dispatch(adminLogout());
    navigate('/admin/login');
  };

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-800/50 border-r border-slate-700">
        <div className="p-4 border-b border-slate-700">
          <h1 className="text-xl font-bold">🔐 管理面板</h1>
          <p className="text-xs text-slate-400 mt-1">v0.9.0</p>
        </div>

        <nav className="p-2">
          <NavLink
            to="/admin"
            end
            className={({ isActive }) =>
              `block px-4 py-2 rounded-lg mb-1 transition-colors ${
                isActive
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'hover:bg-slate-700/50'
              }`
            }
          >
            📊 概览
          </NavLink>

          <NavLink
            to="/admin/users"
            className={({ isActive }) =>
              `block px-4 py-2 rounded-lg mb-1 transition-colors ${
                isActive
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'hover:bg-slate-700/50'
              }`
            }
          >
            👥 用户管理
          </NavLink>

          <NavLink
            to="/admin/feishu"
            className={({ isActive }) =>
              `block px-4 py-2 rounded-lg mb-1 transition-colors ${
                isActive
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'hover:bg-slate-700/50'
              }`
            }
          >
            🔗 飞书配置
          </NavLink>

          <NavLink
            to="/admin/settings"
            className={({ isActive }) =>
              `block px-4 py-2 rounded-lg mb-1 transition-colors ${
                isActive
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'hover:bg-slate-700/50'
              }`
            }
          >
            ⚙️ 系统设置
          </NavLink>
        </nav>

        <div className="absolute bottom-0 left-0 w-64 p-4 border-t border-slate-700">
          <Button variant="ghost" size="sm" onClick={handleLogout} className="w-full">
            🚪 退出登录
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-y-auto">
        <Routes>
          <Route index element={<OverviewPanel stats={stats} userCount={users.length} />} />
          <Route path="users" element={<UsersPanel users={users} />} />
          <Route path="feishu" element={<FeishuPanel />} />
          <Route path="settings" element={<SettingsPanel />} />
        </Routes>
      </main>
    </div>
  );
}

interface OverviewPanelProps {
  stats: { userCount: number; todayRequests: number; version: string } | null;
  userCount: number;
}

function OverviewPanel({ stats, userCount }: OverviewPanelProps) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">📊 系统概览</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          icon="👥"
          label="注册用户"
          value={stats?.userCount ?? userCount}
        />
        <StatCard icon="📝" label="今日请求" value={stats?.todayRequests ?? 0} />
        <StatCard icon="🏷️" label="版本" value={stats?.version ?? 'v0.9.0'} />
      </div>

      <Card>
        <CardTitle>快速开始</CardTitle>
        <ul className="space-y-2 text-slate-400">
          <li>1. 在「飞书配置」中设置应用凭据</li>
          <li>2. 在「用户管理」中查看已注册用户</li>
          <li>3. 在「系统设置」中修改管理员密码</li>
        </ul>
      </Card>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: string;
  label: string;
  value: number | string;
}) {
  return (
    <Card className="text-center">
      <div className="text-4xl mb-2">{icon}</div>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-sm text-slate-400">{label}</div>
    </Card>
  );
}

interface UsersPanelProps {
  users: Array<{
    openId: string;
    name: string;
    email?: string;
    isActive: boolean;
    createdAt: string;
  }>;
}

function UsersPanel({ users }: UsersPanelProps) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">👥 用户管理</h2>

      {users.length === 0 ? (
        <Card className="text-center py-12">
          <div className="text-6xl mb-4">📭</div>
          <p className="text-slate-400">暂无用户</p>
        </Card>
      ) : (
        <Card padding="sm">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left p-3 text-slate-400 font-medium">用户</th>
                <th className="text-left p-3 text-slate-400 font-medium">邮箱</th>
                <th className="text-left p-3 text-slate-400 font-medium">状态</th>
                <th className="text-left p-3 text-slate-400 font-medium">注册时间</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.openId} className="border-b border-slate-700/50">
                  <td className="p-3">{user.name}</td>
                  <td className="p-3 text-slate-400">{user.email || '-'}</td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        user.isActive
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}
                    >
                      {user.isActive ? '活跃' : '禁用'}
                    </span>
                  </td>
                  <td className="p-3 text-slate-400 text-sm">
                    {new Date(user.createdAt).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function FeishuPanel() {
  const [appId, setAppId] = useState('');
  const [appSecret, setAppSecret] = useState('');
  const [redirectUri, setRedirectUri] = useState('');
  const [secretConfigured, setSecretConfigured] = useState(false);
  const [loading, setLoading] = useState(false);
  const [configLoading, setConfigLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(
    null
  );

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setConfigLoading(true);
    try {
      const response = await adminApi.get<{
        app_id?: string;
        redirect_uri?: string;
        app_secret_configured?: boolean;
      }>('/api/admin/feishu/config');
      setAppId(response.data.app_id || '');
      setRedirectUri(response.data.redirect_uri || '');
      setSecretConfigured(response.data.app_secret_configured || false);
    } catch {
      // Ignore - config might not exist yet
    } finally {
      setConfigLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      await adminApi.post('/api/admin/feishu/config', {
        app_id: appId,
        app_secret: appSecret || undefined,
        redirect_uri: redirectUri,
      });
      setMessage({ type: 'success', text: '配置已保存' });
      setAppSecret('');
    } catch {
      setMessage({ type: 'error', text: '保存失败' });
    } finally {
      setLoading(false);
    }
  };

  if (configLoading) {
    return (
      <div>
        <h2 className="text-2xl font-bold mb-6">🔗 飞书配置</h2>
        <Card className="max-w-lg text-center py-8">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">加载配置中...</p>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">🔗 飞书配置</h2>

      <Card className="max-w-lg">
        {/* 配置状态提示 */}
        {appId && (
          <div className="mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
            <p className="text-sm text-green-400">
              ✅ 飞书应用已配置 (App ID: {appId.substring(0, 10)}...)
            </p>
            {secretConfigured && (
              <p className="text-xs text-green-400/70 mt-1">
                App Secret 已设置
              </p>
            )}
          </div>
        )}
        
        {!appId && (
          <div className="mb-4 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <p className="text-sm text-yellow-400">
              ⚠️ 飞书应用尚未配置
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="App ID"
            value={appId}
            onChange={(e) => setAppId(e.target.value)}
            placeholder="cli_xxxxxx"
          />

          <Input
            label={secretConfigured ? "App Secret (已配置，留空则不修改)" : "App Secret"}
            type="password"
            value={appSecret}
            onChange={(e) => setAppSecret(e.target.value)}
            placeholder={secretConfigured ? "••••••••（已配置）" : "请输入 App Secret"}
          />

          <Input
            label="回调地址"
            type="url"
            value={redirectUri}
            onChange={(e) => setRedirectUri(e.target.value)}
            placeholder="https://your-domain.com/auth/feishu/callback"
          />

          {message && (
            <p
              className={`text-sm ${
                message.type === 'success' ? 'text-green-400' : 'text-red-400'
              }`}
            >
              {message.text}
            </p>
          )}

          <Button type="submit" loading={loading} className="w-full">
            保存配置
          </Button>
        </form>
      </Card>
    </div>
  );
}

function SettingsPanel() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(
    null
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: '两次输入的密码不一致' });
      return;
    }

    if (newPassword.length < 6) {
      setMessage({ type: 'error', text: '密码长度至少 6 位' });
      return;
    }

    setLoading(true);

    try {
      await adminApi.post('/api/admin/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      });
      setMessage({ type: 'success', text: '密码已修改' });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch {
      setMessage({ type: 'error', text: '修改失败，请检查原密码' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">⚙️ 系统设置</h2>

      <Card className="max-w-lg">
        <CardTitle>修改管理员密码</CardTitle>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <Input
            label="当前密码"
            type="password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            required
          />

          <Input
            label="新密码"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="至少 6 位"
            required
          />

          <Input
            label="确认新密码"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          {message && (
            <p
              className={`text-sm ${
                message.type === 'success' ? 'text-green-400' : 'text-red-400'
              }`}
            >
              {message.text}
            </p>
          )}

          <Button type="submit" loading={loading} className="w-full">
            修改密码
          </Button>
        </form>
      </Card>
    </div>
  );
}
