import { useState, lazy, Suspense, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import TitleGenerator from './components/TitleGenerator';
import TitleOptimizer from './components/TitleOptimizer';
import TrendPanel from './components/TrendPanel';
import FeedbackPanel from './components/FeedbackPanel';
import ScriptPanel from './components/ScriptPanel';
import CoverPanel from './components/CoverPanel';
import PublishPanel from './components/PublishPanel';
import PipelinePanel from './components/PipelinePanel';
import AnalyticsPanel from './components/AnalyticsPanel';
import HistoryPanel from './components/HistoryPanel';
import HotSearchPanel from './components/HotSearchPanel';
import StrategyPanel from './components/StrategyPanel';
import GrowthLoopPanel from './components/GrowthLoopPanel';
import PublishExecPanel from './components/PublishExecPanel';
import AccountsPanel from './components/AccountsPanel';
// v1.4: 新增组件
import LoginPage from './components/LoginPage';
import ContentReviewPanel from './components/ContentReviewPanel';
import SchedulePanel from './components/SchedulePanel';
import CostDashboard from './components/CostDashboard';
import ABTestPanel from './components/ABTestPanel';
import CompetitorPanel from './components/CompetitorPanel';
import TeamPanel from './components/TeamPanel';
import OnboardingGuide from './components/OnboardingGuide';
import DailyDigestPanel from './components/DailyDigestPanel';
import PlatformSyncPanel from './components/PlatformSyncPanel';

const DashboardPage = lazy(() => import('./components/DashboardPage'));

const NAV_ITEMS = [
  { id: 'dashboard',   label: '数据大屏', icon: '🌐', group: '总览' },
  { id: 'hot',         label: '实时热搜', icon: '🔥', group: '数据' },
  { id: 'trends',      label: '趋势分析', icon: '📊', group: '数据' },
  { id: 'competitor',  label: '竞品监控', icon: '👁', group: '数据' },
  { id: 'daily_digest',label: '每日热点', icon: '📰', group: '数据' },
  { id: 'strategy',    label: '策略中心', icon: '🧠', group: '策略' },
  { id: 'generate',    label: '标题生成', icon: '✍️', group: '创作' },
  { id: 'optimize',    label: '标题优化', icon: '🔧', group: '创作' },
  { id: 'script',      label: '脚本生成', icon: '📝', group: '创作' },
  { id: 'cover',       label: '封面设计', icon: '🎨', group: '创作' },
  { id: 'feedback',    label: '评论分析', icon: '💬', group: '运营' },
  { id: 'review',      label: '内容审核', icon: '📋', group: '运营' },
  { id: 'publish',     label: '发布策略', icon: '📡', group: '运营' },
  { id: 'publish_exec',label: '多平台发布', icon: '🚀', group: '运营' },
  { id: 'pipeline',    label: '全流程',   icon: '⚡', group: '运营' },
  { id: 'schedule',    label: '定时任务', icon: '⏰', group: '运营' },
  { id: 'abtest',      label: 'A/B 测试', icon: '🧪', group: '增长' },
  { id: 'analytics',   label: '数据分析', icon: '📈', group: '增长' },
  { id: 'growth_loop', label: '增长闭环', icon: '🔄', group: '增长' },
  { id: 'history',     label: '历史记录', icon: '📜', group: '增长' },
  { id: 'cost',        label: '成本控制', icon: '💰', group: '设置' },
  { id: 'accounts',    label: '账号管理', icon: '🔗', group: '设置' },
  { id: 'platform_sync', label: '平台同步', icon: '🔌', group: '设置' },
  { id: 'team',        label: '团队管理', icon: '👥', group: '设置' },
];

const GROUPS = ['总览', '数据', '策略', '创作', '运营', '增长', '设置'];

const PANEL_MAP = {
  dashboard:     DashboardPage,
  hot:           HotSearchPanel,
  generate:      TitleGenerator,
  optimize:      TitleOptimizer,
  trends:        TrendPanel,
  strategy:      StrategyPanel,
  feedback:      FeedbackPanel,
  script:        ScriptPanel,
  cover:         CoverPanel,
  publish:       PublishPanel,
  publish_exec:  PublishExecPanel,
  pipeline:      PipelinePanel,
  analytics:     AnalyticsPanel,
  growth_loop:   GrowthLoopPanel,
  history:       HistoryPanel,
  accounts:      AccountsPanel,
  // v1.4 新增
  review:        ContentReviewPanel,
  schedule:      SchedulePanel,
  cost:          CostDashboard,
  abtest:        ABTestPanel,
  competitor:    CompetitorPanel,
  team:          TeamPanel,
  daily_digest:  DailyDigestPanel,
  platform_sync: PlatformSyncPanel,
};

// 路由 ID 到导航 ID 的映射
const ROUTE_TO_NAV = {
  '/': 'dashboard',
  '/accounts': 'accounts',
  '/pipeline': 'pipeline',
  '/trends': 'trends',
  '/schedules': 'schedule',
  '/team': 'team',
};

export default function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [active, setActive] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // 检查本地存储的登录状态
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
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
    setActive('dashboard');
  };

  const handleNavigate = (route) => {
    const navId = ROUTE_TO_NAV[route];
    if (navId) setActive(navId);
  };

  // 未登录 → 显示登录页
  if (!user || !token) {
    return <LoginPage onLogin={handleLogin} />;
  }

  const Panel = PANEL_MAP[active] || DashboardPage;
  const isDashboard = active === 'dashboard';

  if (isDashboard) {
    return (
      <div className="flex h-screen overflow-hidden">
        <Sidebar
          items={NAV_ITEMS}
          groups={GROUPS}
          active={active}
          onSelect={setActive}
          open={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />
        <div className={`flex-1 min-w-0 overflow-auto transition-[padding] duration-300 ${sidebarOpen ? 'pl-64' : 'pl-0'}`}>
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="fixed top-4 left-4 z-50 p-2 rounded-xl bg-panel-50/80 backdrop-blur-sm border border-panel-border text-txt-muted hover:text-txt-primary hover:bg-panel-100 transition-colors"
              title="展开侧边栏"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </button>
          )}
          <Suspense fallback={
            <div className="flex items-center justify-center h-screen bg-panel">
              <div className="text-center">
                <div className="inline-block w-10 h-10 border-4 border-brand-500/30 border-t-brand-400 rounded-full animate-spin mb-4" />
                <p className="text-txt-secondary text-sm">数据大屏加载中...</p>
              </div>
            </div>
          }>
            <OnboardingGuide onNavigate={handleNavigate} />
            <DashboardPage user={user} onLogout={handleLogout} />
          </Suspense>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-panel grid-bg">
      <Sidebar
        items={NAV_ITEMS}
        groups={GROUPS}
        active={active}
        onSelect={setActive}
        open={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      <div className="flex flex-1 flex-col min-w-0">
        <Header
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
          sidebarOpen={sidebarOpen}
          user={user}
          onLogout={handleLogout}
        />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            <OnboardingGuide onNavigate={handleNavigate} />
            <Panel />
          </div>
        </main>
      </div>
    </div>
  );
}
