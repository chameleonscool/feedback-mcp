import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from '@/hooks/useAppDispatch';
import { adminLogin } from './adminSlice';
import { Button, Card, CardTitle, CardDescription, Input } from '@/components/ui';

export default function AdminLoginPage() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await dispatch(adminLogin({ username, password })).unwrap();
      navigate('/admin');
    } catch {
      setError('用户名或密码错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardTitle>🔐 管理员登录</CardTitle>
        <CardDescription>请输入管理员凭据</CardDescription>

        <form onSubmit={handleSubmit} className="space-y-4 mt-6">
          <Input
            label="用户名"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="admin"
            required
            autoComplete="username"
          />

          <Input
            label="密码"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            autoComplete="current-password"
            error={error}
          />

          <div className="pt-4 space-y-3">
            <Button type="submit" loading={loading} className="w-full">
              登录
            </Button>

            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate('/login')}
              className="w-full"
            >
              ← 返回
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
