import { useState, lazy, Suspense, useEffect } from 'react';
import LoginPage from './components/LoginPage';
import ForgotPasswordPage from './components/ForgotPasswordPage';

const EnterpriseDashboard = lazy(() => import('./components/EnterpriseDashboard'));
const AICOOPage = lazy(() => import('./components/AICOOPage'));
const AgentsPage = lazy(() => import('./components/AgentsPage'));
const GrowthBrainPage = lazy(() => import('./components/GrowthBrainPage'));
const DataCollectionPage = lazy(() => import('./components/DataCollectionPage'));
const ToolsPage = lazy(() => import('./components/ToolsPage'));
const KnowledgePage = lazy(() => import('./components/KnowledgePage'));
const AIAssistantPage = lazy(() => import('./components/AIAssistantPage'));
const SettingsPage = lazy(() => import('./components/SettingsPage'));

const NAV_ITEMS = [
  { id: 'dashboard',   label: '运营工作台', icon: '📊', group: '经营' },
  { id: 'data',        label: '市场与竞品', icon: '🔎', group: '经营' },
  { id: 'tools',       label: '内容生产',   icon: '✍️', group: '执行' },
  { id: 'brain',       label: '效果复盘',   icon: '📈', group: '执行' },
  { id: 'assistant',   label: '运营助手',   icon: '💬', group: '智能' },
  { id: 'coo',         label: '任务调度',   icon: '🎯', group: '智能' },
  { id: 'knowledge',   label: '知识与商品', icon: '📚', group: '配置' },
  { id: 'settings',    label: '系统配置',   icon: '⚙️', group: '配置' },
];

const GROUPS = ['经营', '执行', '智能', '配置'];

const PAGE_MAP = {
  dashboard:  EnterpriseDashboard,
  assistant:  AIAssistantPage,
  coo:        AICOOPage,
  agents:     AgentsPage,
  data:       DataCollectionPage,
  brain:      GrowthBrainPage,
  tools:      ToolsPage,
  knowledge:  KnowledgePage,
  settings:   SettingsPage,
};

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-screen dashboard-container">
      <div className="text-center">
        <div className="inline-block w-12 h-12 border-4 border-brand-500/30 border-t-brand-400 rounded-full animate-spin mb-4" />
        <p className="text-txt-secondary text-sm">加载中...</p>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [active, setActive] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [authView, setAuthView] = useState('login');

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
  }, []);

  const handleLogin = (userData, accessToken) => {
    setUser(userData);
    setToken(accessToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
    setActive('dashboard');
  };

  if (!user || !token) {
    if (authView === 'forgotPassword') {
      return <ForgotPasswordPage onBack={() => setAuthView('login')} />;
    }
    return (
      <LoginPage
        onLogin={handleLogin}
        onForgotPassword={() => setAuthView('forgotPassword')}
      />
    );
  }

  const Page = PAGE_MAP[active] || EnterpriseDashboard;

  return (
    <div className="flex h-screen overflow-hidden dashboard-container">
      {/* 侧边栏 */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 flex-shrink-0 overflow-hidden`}>
        <div className="w-64 h-full flex flex-col bg-panel-50/80 backdrop-blur-xl border-r border-panel-border">
          {/* Logo */}
          <div className="p-5 border-b border-panel-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-[0_0_15px_rgba(34,211,138,0.3)]">
                E
              </div>
              <div>
                <h1 className="text-base font-bold text-white">EchoFlow AI</h1>
                <p className="text-xs text-brand-400">Enterprise v3.0</p>
              </div>
            </div>
          </div>

          {/* 导航 */}
          <nav className="flex-1 overflow-y-auto p-3 space-y-1">
            {GROUPS.map((group) => (
              <div key={group} className="mb-2">
                <p className="px-3 py-2 text-xs font-semibold text-txt-muted uppercase tracking-wider">{group}</p>
                {NAV_ITEMS.filter(item => item.group === group).map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActive(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 ${
                      active === item.id
                        ? 'bg-brand-500/15 text-brand-300 font-medium shadow-[0_0_10px_rgba(34,211,238,0.1)]'
                        : 'text-txt-secondary hover:bg-panel-100 hover:text-txt-primary'
                    }`}
                  >
                    <span className="text-lg">{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            ))}
          </nav>

          {/* 底部用户信息 */}
          <div className="p-4 border-t border-panel-border">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center">
                <span className="text-sm">👤</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user.username || 'Admin'}</p>
                <p className="text-xs text-txt-muted">{user.role || '管理员'}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-1.5 rounded-lg text-txt-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
                title="退出登录"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* 折叠状态下的展开按钮 */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed top-4 left-4 z-50 p-2.5 rounded-xl bg-panel-50/80 backdrop-blur-sm border border-panel-border text-txt-muted hover:text-brand-400 hover:bg-panel-100 transition-colors"
          title="展开侧边栏"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          </svg>
        </button>
      )}

      {/* 主内容区 */}
      <main className="flex-1 min-w-0 overflow-y-auto">
        <Suspense fallback={<LoadingFallback />}>
          <Page />
        </Suspense>
      </main>

      {/* 侧边栏折叠按钮 */}
      {sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(false)}
          className="fixed bottom-4 left-4 z-50 p-2 rounded-lg bg-panel-50/60 backdrop-blur-sm border border-panel-border text-txt-muted hover:text-brand-400 transition-colors"
          title="收起侧边栏"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M18.75 19.5l-7.5-7.5 7.5-7.5m-6 15L5.25 12l7.5-7.5" />
          </svg>
        </button>
      )}
    </div>
  );
}
