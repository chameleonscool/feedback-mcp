import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch';
import { loadCachedAuth } from '@/features/auth/authSlice';
import { loadCachedSession } from '@/features/admin/adminSlice';
import { api } from '@/services/api';

// Pages
import LoginPage from '@/features/auth/LoginPage';
import AdminLoginPage from '@/features/admin/AdminLoginPage';
import InitPage from '@/features/admin/InitPage';
import TasksPage from '@/features/tasks/TasksPage';
import AdminDashboard from '@/features/admin/AdminDashboard';

interface SystemStatus {
  initialized: boolean;
  admin_exists: boolean;
  feishu_configured: boolean;
}

function App() {
  const dispatch = useAppDispatch();
  const location = useLocation();
  const { isAuthenticated: userAuth } = useAppSelector((state) => state.auth);
  const { isAuthenticated: adminAuth } = useAppSelector((state) => state.admin);

  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 加载缓存的认证状态
    dispatch(loadCachedAuth());
    dispatch(loadCachedSession());

    // 检查系统状态
    checkSystemStatus();
  }, [dispatch]);

  const checkSystemStatus = async () => {
    try {
      const response = await api.get<SystemStatus>('/api/status');
      setSystemStatus(response.data);
    } catch {
      // 如果 /api/status 不可用，假设系统已初始化
      setSystemStatus({
        initialized: true,
        admin_exists: true,
        feishu_configured: true,
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">加载中...</p>
        </div>
      </div>
    );
  }

  // 如果系统未初始化，重定向到初始化页面
  if (
    systemStatus &&
    !systemStatus.initialized &&
    location.pathname !== '/init'
  ) {
    return <Navigate to="/init" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <Routes>
        {/* 初始化 */}
        <Route path="/init" element={<InitPage />} />

        {/* 认证 */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />

        {/* 管理员面板 */}
        <Route
          path="/admin/*"
          element={
            adminAuth ? (
              <AdminDashboard />
            ) : (
              <Navigate to="/admin/login" replace />
            )
          }
        />

        {/* 用户任务页面 */}
        <Route
          path="/*"
          element={
            userAuth ? <TasksPage /> : <Navigate to="/login" replace />
          }
        />
      </Routes>
    </div>
  );
}

export default App;
