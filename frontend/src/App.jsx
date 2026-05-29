import { useState } from 'react';
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

const NAV_ITEMS = [
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

const GROUPS = ['数据', '策略', '创作', '运营', '增长'];

const PANEL_MAP = {
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
  const [active, setActive] = useState('hot');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const Panel = PANEL_MAP[active] || TitleGenerator;

  return (
    <div className="flex h-screen overflow-hidden bg-surface-50">
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
          <div className="max-w-6xl mx-auto animate-fade-in">
            <Panel />
          </div>
        </main>
      </div>
    </div>
  );
}
