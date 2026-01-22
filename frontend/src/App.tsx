import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch';
import { loadCachedAuth } from '@/features/auth/authSlice';

// Pages (will be created later)
import LoginPage from '@/features/auth/LoginPage';

function App() {
  const dispatch = useAppDispatch();
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // 页面加载时检查缓存的认证信息
    dispatch(loadCachedAuth());
  }, [dispatch]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <MainLayout />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </div>
  );
}

// Placeholder for main layout
function MainLayout() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">🚧 开发中</h1>
        <p className="text-slate-400">任务页面即将上线</p>
      </div>
    </div>
  );
}

export default App;
