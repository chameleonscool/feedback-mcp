import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, CardTitle, CardDescription, Input } from '@/components/ui';
import { api } from '@/services/api';

type InitStep = 'loading' | 'admin' | 'feishu' | 'complete';

interface SystemStatus {
  initialized: boolean;
  admin_exists: boolean;
  feishu_configured: boolean;
}

export default function InitPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<InitStep>('loading');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Admin credentials
  const [adminUsername, setAdminUsername] = useState('admin');
  const [adminPassword, setAdminPassword] = useState('');
  const [adminPasswordConfirm, setAdminPasswordConfirm] = useState('');

  // Feishu config
  const [appId, setAppId] = useState('');
  const [appSecret, setAppSecret] = useState('');
  const [redirectUri, setRedirectUri] = useState('');

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await api.get<SystemStatus>('/api/system/status');
      const status = response.data;

      if (status.initialized) {
        navigate('/login');
        return;
      }

      if (!status.admin_exists) {
        setStep('admin');
      } else if (!status.feishu_configured) {
        setStep('feishu');
      } else {
        setStep('complete');
      }
    } catch {
      setStep('admin');
    }
  };

  const handleAdminSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (adminPassword !== adminPasswordConfirm) {
      setError('两次输入的密码不一致');
      return;
    }

    if (adminPassword.length < 6) {
      setError('密码长度至少 6 位');
      return;
    }

    setLoading(true);
    try {
      await api.post('/api/system/initialize', {
        username: adminUsername,
        password: adminPassword,
      });
      setStep('feishu');
    } catch {
      setError('设置管理员失败');
    } finally {
      setLoading(false);
    }
  };

  const handleFeishuSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/api/admin/feishu/config', {
        app_id: appId,
        app_secret: appSecret,
        redirect_uri: redirectUri,
      });
      setStep('complete');
    } catch {
      setError('配置飞书应用失败');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = () => {
    navigate('/login');
  };

  if (step === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">检查系统状态...</p>
        </div>
      </div>
    );
  }

  if (step === 'complete') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <div className="text-6xl mb-4">🎉</div>
          <CardTitle>初始化完成</CardTitle>
          <CardDescription>系统已准备就绪</CardDescription>

          <div className="mt-8">
            <Button onClick={handleComplete} className="w-full">
              开始使用
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        {/* Progress indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <StepIndicator
            step={1}
            label="管理员"
            active={step === 'admin'}
            completed={step !== 'admin'}
          />
          <div className="w-12 h-0.5 bg-slate-700" />
          <StepIndicator
            step={2}
            label="飞书配置"
            active={step === 'feishu'}
            completed={false}
          />
        </div>

        {step === 'admin' && (
          <>
            <CardTitle>👤 设置管理员</CardTitle>
            <CardDescription>创建管理员账号以管理系统</CardDescription>

            <form onSubmit={handleAdminSetup} className="space-y-4 mt-6">
              <Input
                label="用户名"
                type="text"
                value={adminUsername}
                onChange={(e) => setAdminUsername(e.target.value)}
                placeholder="admin"
                required
              />

              <Input
                label="密码"
                type="password"
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                placeholder="至少 6 位"
                required
              />

              <Input
                label="确认密码"
                type="password"
                value={adminPasswordConfirm}
                onChange={(e) => setAdminPasswordConfirm(e.target.value)}
                placeholder="再次输入密码"
                required
                error={error}
              />

              <div className="pt-4">
                <Button type="submit" loading={loading} className="w-full">
                  下一步 →
                </Button>
              </div>
            </form>
          </>
        )}

        {step === 'feishu' && (
          <>
            <CardTitle>🔗 配置飞书应用</CardTitle>
            <CardDescription>
              在{' '}
              <a
                href="https://open.feishu.cn/app"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline"
              >
                飞书开放平台
              </a>{' '}
              创建应用并获取凭据
            </CardDescription>

            <form onSubmit={handleFeishuSetup} className="space-y-4 mt-6">
              <Input
                label="App ID"
                type="text"
                value={appId}
                onChange={(e) => setAppId(e.target.value)}
                placeholder="cli_xxxxxx"
                required
              />

              <Input
                label="App Secret"
                type="password"
                value={appSecret}
                onChange={(e) => setAppSecret(e.target.value)}
                placeholder="xxxxxx"
                required
              />

              <Input
                label="回调地址"
                type="url"
                value={redirectUri}
                onChange={(e) => setRedirectUri(e.target.value)}
                placeholder="https://your-domain.com/auth/feishu/callback"
                required
                error={error}
              />

              <div className="pt-4 space-y-3">
                <Button type="submit" loading={loading} className="w-full">
                  完成配置
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setStep('complete')}
                  className="w-full"
                >
                  稍后配置
                </Button>
              </div>
            </form>
          </>
        )}
      </Card>
    </div>
  );
}

function StepIndicator({
  step,
  label,
  active,
  completed,
}: {
  step: number;
  label: string;
  active: boolean;
  completed: boolean;
}) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={`
          w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
          transition-colors duration-200
          ${
            completed
              ? 'bg-green-500 text-white'
              : active
              ? 'bg-blue-500 text-white'
              : 'bg-slate-700 text-slate-400'
          }
        `}
      >
        {completed ? '✓' : step}
      </div>
      <span
        className={`text-xs mt-1 ${
          active ? 'text-white' : 'text-slate-500'
        }`}
      >
        {label}
      </span>
    </div>
  );
}
