import React, { useEffect } from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  useNavigate,
} from 'react-router-dom';
import { ConfigProvider, Spin, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAuthStore } from './store/authStore';

import AuthLayout from './components/Layout/AuthLayout';
import MainLayout from './components/Layout/MainLayout';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import DatasetsPage from './pages/Datasets';
import DatasetDetail from './pages/Datasets/Detail';
import ChatPage from './pages/Chat';
import SettingsPage from './pages/Settings';
import AdminPage from './pages/Admin';

/** 路由守卫：未登录跳转到登录页 */
const ProtectedRoute: React.FC = () => {
  const { user, initialized } = useAuthStore();

  if (!initialized) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

/** 管理后台守卫：仅 admin 可访问 */
const AdminRoute: React.FC = () => {
  const { user } = useAuthStore();

  if (user?.role !== 'admin') {
    return <Navigate to="/datasets" replace />;
  }

  return <Outlet />;
};

/** 已登录用户访问登录页时跳转首页 */
const PublicRoute: React.FC = () => {
  const { user, initialized } = useAuthStore();

  if (!initialized) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <Spin size="large" />
      </div>
    );
  }

  if (user) {
    return <Navigate to="/datasets" replace />;
  }

  return <Outlet />;
};

/** 监听 auth:unauthorized 事件，软导航到登录页 */
const AuthWatcher: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handler = () => navigate('/login', { replace: true });
    window.addEventListener('auth:unauthorized', handler);
    return () => window.removeEventListener('auth:unauthorized', handler);
  }, [navigate]);

  return null;
};

const App: React.FC = () => {
  const initialize = useAuthStore((s) => s.initialize);

  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <BrowserRouter>
        <AuthWatcher />
        <Routes>
          {/* 公开路由（未登录） */}
          <Route element={<PublicRoute />}>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>
          </Route>

          {/* 受保护路由（需登录） */}
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/datasets" element={<DatasetsPage />} />
              <Route path="/datasets/:id" element={<DatasetDetail />} />
              <Route path="/conversations" element={<ChatPage />} />
              <Route path="/conversations/:id" element={<ChatPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              {/* 管理后台 */}
              <Route element={<AdminRoute />}>
                <Route path="/admin" element={<AdminPage />} />
              </Route>
            </Route>
          </Route>

          {/* 默认重定向 */}
          <Route path="*" element={<Navigate to="/datasets" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
