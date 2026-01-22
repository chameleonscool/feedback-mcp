import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch';
import { setApiKey, loadCachedAuth } from './authSlice';
import { fetchUserInfo } from '@/features/user/userSlice';
import { Button, Card, CardTitle, CardDescription } from '@/components/ui';
import { getApiKey, getRemainingDays } from '@/utils/storage';

type ViewState = 'loading' | 'login' | 'cached' | 'admin-login';

export default function LoginPage() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const { profile } = useAppSelector((state) => state.user);

  const [viewState, setViewState] = useState<ViewState>('loading');
  const [remainingDays, setRemainingDays] = useState(0);

  useEffect(() => {
    // 检查是否有缓存的 API Key
    const cachedApiKey = getApiKey();
    
    if (cachedApiKey) {
      // 有缓存，验证是否有效
      dispatch(loadCachedAuth());
      dispatch(fetchUserInfo())
        .unwrap()
        .then(() => {
          setRemainingDays(getRemainingDays());
          setViewState('cached');
        })
        .catch(() => {
          setViewState('login');
        });
    } else {
      setViewState('login');
    }
  }, [dispatch]);

  useEffect(() => {
    // 检查 URL 中是否有 api_key 参数（OAuth 回调）
    const urlParams = new URLSearchParams(window.location.search);
    const apiKeyFromUrl = urlParams.get('api_key');

    if (apiKeyFromUrl?.startsWith('uk_')) {
      dispatch(setApiKey(apiKeyFromUrl));
      // 清除 URL 参数
      window.history.replaceState({}, '', window.location.pathname);
      navigate('/');
    }
  }, [dispatch, navigate]);

  useEffect(() => {
    // 如果已认证，跳转到主页
    if (isAuthenticated && viewState !== 'cached') {
      navigate('/');
    }
  }, [isAuthenticated, viewState, navigate]);

  const handleFeishuLogin = () => {
    window.location.href = '/auth/feishu/login';
  };

  const handleContinue = () => {
    navigate('/');
  };

  const handleSwitchAccount = () => {
    // 清除缓存并重新登录
    dispatch({ type: 'auth/clearAuth' });
    dispatch({ type: 'user/clearProfile' });
    setViewState('login');
  };

  const handleGuestMode = () => {
    navigate('/');
  };

  // Loading state
  if (viewState === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">加载中...</p>
        </div>
      </div>
    );
  }

  // Cached login view
  if (viewState === 'cached') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <CardTitle>👋 欢迎回来</CardTitle>
          <CardDescription>您的登录状态仍然有效</CardDescription>

          <div className="py-6">
            <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-3xl mb-4">
              {profile?.avatarUrl ? (
                <img
                  src={profile.avatarUrl}
                  alt="avatar"
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                '👤'
              )}
            </div>
            <h3 className="text-xl font-semibold text-white">
              {profile?.name || '用户'}
            </h3>
            <p className="text-sm text-slate-400 mt-1">
              登录有效期还剩 {remainingDays} 天
            </p>
          </div>

          <div className="space-y-3">
            <Button onClick={handleContinue} className="w-full">
              ✨ 继续使用
            </Button>
            <Button
              variant="secondary"
              onClick={handleSwitchAccount}
              className="w-full"
            >
              🔄 切换账号
            </Button>
            <Button
              variant="ghost"
              onClick={handleSwitchAccount}
              className="w-full"
            >
              🚪 退出登录
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Login view
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md text-center">
        <CardTitle>🤖 AI Intent Center</CardTitle>
        <CardDescription>AI 意图收集系统</CardDescription>

        <div className="space-y-3 mt-8">
          <Button onClick={handleFeishuLogin} className="w-full">
            <FeishuIcon />
            使用飞书登录
          </Button>

          <div className="relative py-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-700" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-slate-800 text-slate-500">或</span>
            </div>
          </div>

          <Button
            variant="secondary"
            onClick={() => setViewState('admin-login')}
            className="w-full"
          >
            🔐 管理员登录
          </Button>

          <Button variant="ghost" onClick={handleGuestMode} className="w-full">
            💻 使用 Web UI（无需登录）
          </Button>
        </div>
      </Card>
    </div>
  );
}

function FeishuIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="mr-1"
    >
      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  );
}
