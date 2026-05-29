import { useState, lazy, Suspense } from 'react';
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

const DashboardPage = lazy(() => import('./components/DashboardPage'));

const NAV_ITEMS = [
  { id: 'dashboard',   label: '数据大屏', icon: '🌐', group: '总览' },
  { id: 'hot',         label: '实时热搜', icon: '🔥', group: '数据' },
  { id: 'trends',      label: '趋势分析', icon: '📊', group: '数据' },
  { id: 'strategy',    label: '策略中心', icon: '🧠', group: '策略' },
  { id: 'generate',    label: '标题生成', icon: '✍️', group: '创作' },
  { id: 'optimize',    label: '标题优化', icon: '🔧', group: '创作' },
  { id: 'script',      label: '脚本生成', icon: '📝', group: '创作' },
  { id: 'cover',       label: '封面设计', icon: '🎨', group: '创作' },
  { id: 'feedback',    label: '评论分析', icon: '💬', group: '运营' },
  { id: 'publish',     label: '发布策略', icon: '📡', group: '运营' },
  { id: 'pipeline',    label: '全流程',   icon: '🚀', group: '运营' },
  { id: 'analytics',   label: '数据分析', icon: '📈', group: '增长' },
  { id: 'growth_loop', label: '增长闭环', icon: '🔄', group: '增长' },
  { id: 'history',     label: '历史记录', icon: '📋', group: '增长' },
];

const GROUPS = ['总览', '数据', '策略', '创作', '运营', '增长'];

const PANEL_MAP = {
  dashboard:   DashboardPage,
  hot:         HotSearchPanel,
  generate:    TitleGenerator,
  optimize:    TitleOptimizer,
  trends:      TrendPanel,
  strategy:    StrategyPanel,
  feedback:    FeedbackPanel,
  script:      ScriptPanel,
  cover:       CoverPanel,
  publish:     PublishPanel,
  pipeline:    PipelinePanel,
  analytics:   AnalyticsPanel,
  growth_loop: GrowthLoopPanel,
  history:     HistoryPanel,
};

export default function App() {
  const [active, setActive] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const Panel = PANEL_MAP[active] || DashboardPage;
  const isDashboard = active === 'dashboard';

  if (isDashboard) {
    return (
      <div className="flex h-screen overflow-hidden">
        {/* 侧边栏叠加在大屏上 */}
        <Sidebar
          items={NAV_ITEMS}
          groups={GROUPS}
          active={active}
          onSelect={setActive}
          open={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />
        {/* 大屏全屏展示 */}
        <div className="flex-1 min-w-0 overflow-auto">
          <Suspense fallback={
            <div className="flex items-center justify-center h-screen bg-panel">
              <div className="text-center">
                <div className="inline-block w-10 h-10 border-4 border-brand-500/30 border-t-brand-400 rounded-full animate-spin mb-4" />
                <p className="text-txt-secondary text-sm">数据大屏加载中...</p>
              </div>
            </div>
          }>
            <DashboardPage />
          </Suspense>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-panel grid-bg">
      {/* 侧边栏 */}
      <Sidebar
        items={NAV_ITEMS}
        groups={GROUPS}
        active={active}
        onSelect={setActive}
        open={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* 主内容区 */}
      <div className="flex flex-1 flex-col min-w-0">
        <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} sidebarOpen={sidebarOpen} />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            <Panel />
          </div>
        </main>
      </div>
    </div>
  );
}
