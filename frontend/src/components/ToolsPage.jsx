import { useState } from 'react';

// 懒加载所有工具组件
import TitleGenerator from './TitleGenerator';
import TitleOptimizer from './TitleOptimizer';
import TrendPanel from './TrendPanel';
import FeedbackPanel from './FeedbackPanel';
import ScriptPanel from './ScriptPanel';
import CoverPanel from './CoverPanel';
import PipelinePanel from './PipelinePanel';
import AnalyticsPanel from './AnalyticsPanel';
import HistoryPanel from './HistoryPanel';
import HotSearchPanel from './HotSearchPanel';
import StrategyPanel from './StrategyPanel';
import GrowthLoopPanel from './GrowthLoopPanel';
import PublishExecPanel from './PublishExecPanel';
import ContentReviewPanel from './ContentReviewPanel';
import SchedulePanel from './SchedulePanel';
import ABTestPanel from './ABTestPanel';
import CompetitorPanel from './CompetitorPanel';
import DailyDigestPanel from './DailyDigestPanel';
import PublishPanel from './PublishPanel';

const TOOL_GROUPS = [
  {
    name: '数据洞察',
    icon: '📊',
    tools: [
      { id: 'hot', label: '实时热搜', icon: '🔥', component: HotSearchPanel },
      { id: 'trends', label: '趋势分析', icon: '📊', component: TrendPanel },
      { id: 'competitor', label: '竞品监控', icon: '👁', component: CompetitorPanel },
      { id: 'daily_digest', label: '每日热点', icon: '📰', component: DailyDigestPanel },
      { id: 'feedback', label: '评论分析', icon: '💬', component: FeedbackPanel },
      { id: 'analytics', label: '数据分析', icon: '📈', component: AnalyticsPanel },
    ],
  },
  {
    name: '内容创作',
    icon: '✍️',
    tools: [
      { id: 'generate', label: '标题生成', icon: '✍️', component: TitleGenerator },
      { id: 'optimize', label: '标题优化', icon: '🔧', component: TitleOptimizer },
      { id: 'script', label: '脚本生成', icon: '📝', component: ScriptPanel },
      { id: 'cover', label: '封面设计', icon: '🎨', component: CoverPanel },
      { id: 'pipeline', label: '全流程', icon: '⚡', component: PipelinePanel },
    ],
  },
  {
    name: '运营执行',
    icon: '🚀',
    tools: [
      { id: 'strategy', label: '策略中心', icon: '🧠', component: StrategyPanel },
      { id: 'publish', label: '发布策略', icon: '📡', component: PublishPanel },
      { id: 'publish_exec', label: '多平台发布', icon: '🚀', component: PublishExecPanel },
      { id: 'review', label: '内容审核', icon: '📋', component: ContentReviewPanel },
      { id: 'schedule', label: '定时任务', icon: '⏰', component: SchedulePanel },
    ],
  },
  {
    name: '增长优化',
    icon: '🔄',
    tools: [
      { id: 'growth_loop', label: '增长闭环', icon: '🔄', component: GrowthLoopPanel },
      { id: 'abtest', label: 'A/B 测试', icon: '🧪', component: ABTestPanel },
      { id: 'history', label: '历史记录', icon: '📜', component: HistoryPanel },
    ],
  },
];

export default function ToolsPage() {
  const [activeTool, setActiveTool] = useState(null);
  const [activeGroup, setActiveGroup] = useState(null);

  const handleSelectTool = (tool) => {
    setActiveTool(tool);
    setActiveGroup(null);
  };

  const ActiveComponent = activeTool?.component;

  if (ActiveComponent) {
    return (
      <div className="dashboard-container min-h-screen p-6">
        {/* 返回按钮 */}
        <div className="mb-4">
          <button
            onClick={() => setActiveTool(null)}
            className="btn-ghost text-sm"
          >
            ← 返回工具箱
          </button>
          <span className="text-txt-muted mx-3">/</span>
          <span className="text-brand-400 text-sm font-medium">{activeTool.icon} {activeTool.label}</span>
        </div>
        <ActiveComponent />
      </div>
    );
  }

  return (
    <div className="dashboard-container min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white dashboard-glow-text">工具箱</h1>
        <p className="text-txt-secondary mt-1">19个专业工具 · 覆盖内容运营全链路</p>
      </div>

      {/* 工具分组 */}
      <div className="space-y-8">
        {TOOL_GROUPS.map((group) => (
          <div key={group.name}>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">{group.icon}</span>
              <h2 className="text-xl font-bold text-white">{group.name}</h2>
              <span className="text-xs text-txt-muted bg-panel-200 px-2 py-0.5 rounded-full">
                {group.tools.length}个工具
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
              {group.tools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => handleSelectTool(tool)}
                  className="dashboard-panel rounded-2xl p-5 text-center hover:scale-[1.03] transition-all duration-200 group"
                >
                  <span className="text-3xl block mb-3 group-hover:scale-110 transition-transform">{tool.icon}</span>
                  <p className="text-sm font-medium text-white">{tool.label}</p>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
