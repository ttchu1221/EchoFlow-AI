import { lazy, Suspense, useState } from 'react';

const TitleGenerator = lazy(() => import('./TitleGenerator'));
const TitleOptimizer = lazy(() => import('./TitleOptimizer'));
const TrendPanel = lazy(() => import('./TrendPanel'));
const FeedbackPanel = lazy(() => import('./FeedbackPanel'));
const ScriptPanel = lazy(() => import('./ScriptPanel'));
const CoverPanel = lazy(() => import('./CoverPanel'));
const PipelinePanel = lazy(() => import('./PipelinePanel'));
const AnalyticsPanel = lazy(() => import('./AnalyticsPanel'));
const HistoryPanel = lazy(() => import('./HistoryPanel'));
const HotSearchPanel = lazy(() => import('./HotSearchPanel'));
const StrategyPanel = lazy(() => import('./StrategyPanel'));
const GrowthLoopPanel = lazy(() => import('./GrowthLoopPanel'));
const PublishExecPanel = lazy(() => import('./PublishExecPanel'));
const ContentReviewPanel = lazy(() => import('./ContentReviewPanel'));
const SchedulePanel = lazy(() => import('./SchedulePanel'));
const ABTestPanel = lazy(() => import('./ABTestPanel'));
const CompetitorPanel = lazy(() => import('./CompetitorPanel'));
const DailyDigestPanel = lazy(() => import('./DailyDigestPanel'));
const PublishPanel = lazy(() => import('./PublishPanel'));

const TOOL_GROUPS = [
  {
    name: '市场机会',
    summary: '看竞品、看平台、看需求，先判断这件事值不值得做。',
    icon: '🔎',
    tools: [
      { id: 'competitor', label: '竞品监控', icon: '👁', component: CompetitorPanel, level: '核心' },
      { id: 'trends', label: '趋势机会', icon: '📊', component: TrendPanel, level: '核心' },
      { id: 'feedback', label: '需求评论', icon: '💬', component: FeedbackPanel, level: '核心' },
      { id: 'hot', label: '平台热榜', icon: '🔥', component: HotSearchPanel, level: '辅助' },
      { id: 'daily_digest', label: '热点简报', icon: '📰', component: DailyDigestPanel, level: '辅助' },
    ],
  },
  {
    name: '内容转化',
    summary: '围绕商品卖点生成标题、脚本、封面文案和发布策略。',
    icon: '✍️',
    tools: [
      { id: 'pipeline', label: '内容工作流', icon: '⚡', component: PipelinePanel, level: '核心' },
      { id: 'script', label: '带货脚本', icon: '📝', component: ScriptPanel, level: '核心' },
      { id: 'generate', label: '标题生成', icon: '✍️', component: TitleGenerator, level: '核心' },
      { id: 'optimize', label: '标题优化', icon: '🔧', component: TitleOptimizer, level: '辅助' },
      { id: 'cover', label: '封面文案', icon: '🎨', component: CoverPanel, level: '辅助' },
      { id: 'review', label: '内容审核', icon: '📋', component: ContentReviewPanel, level: '辅助' },
    ],
  },
  {
    name: '发布执行',
    summary: '把内容排期、发布动作和平台账号数据串起来。',
    icon: '🚀',
    tools: [
      { id: 'strategy', label: '运营策略', icon: '🧠', component: StrategyPanel, level: '核心' },
      { id: 'publish', label: '发布计划', icon: '📡', component: PublishPanel, level: '核心' },
      { id: 'schedule', label: '采集/发布任务', icon: '⏰', component: SchedulePanel, level: '辅助' },
      { id: 'publish_exec', label: '多平台发布', icon: '🚀', component: PublishExecPanel, level: '待接入' },
    ],
  },
  {
    name: '效果复盘',
    summary: '把播放、互动和转化结果回流，形成下一轮选题依据。',
    icon: '📈',
    tools: [
      { id: 'analytics', label: '经营分析', icon: '📈', component: AnalyticsPanel, level: '核心' },
      { id: 'growth_loop', label: '增长闭环', icon: '🔄', component: GrowthLoopPanel, level: '核心' },
      { id: 'abtest', label: '内容实验', icon: '🧪', component: ABTestPanel, level: '辅助' },
      { id: 'history', label: '操作记录', icon: '📜', component: HistoryPanel, level: '辅助' },
    ],
  },
];

const LEVEL_CLASS = {
  核心: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200',
  辅助: 'border-blue-500/30 bg-blue-500/10 text-blue-200',
  待接入: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
};

export default function ToolsPage() {
  const [activeTool, setActiveTool] = useState(null);

  const handleSelectTool = (tool) => {
    setActiveTool(tool);
  };

  const ActiveComponent = activeTool?.component;

  if (ActiveComponent) {
    return (
      <div className="dashboard-container min-h-screen p-6">
        {/* 返回按钮 */}
        <div className="mb-4">
          <button onClick={() => setActiveTool(null)} className="btn-ghost text-sm">← 返回内容生产</button>
          <span className="text-txt-muted mx-3">/</span>
          <span className="text-brand-400 text-sm font-medium">{activeTool.icon} {activeTool.label}</span>
        </div>
        <Suspense fallback={<div className="dashboard-panel rounded-xl p-6 text-sm text-txt-secondary">加载工具中...</div>}>
          <ActiveComponent />
        </Suspense>
      </div>
    );
  }

  return (
    <div className="dashboard-container min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white dashboard-glow-text">内容生产</h1>
        <p className="text-txt-secondary mt-1">从市场机会到内容转化，再到发布执行和效果复盘</p>
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
            <p className="text-sm text-txt-muted mb-4">{group.summary}</p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {group.tools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => handleSelectTool(tool)}
                  className="dashboard-panel rounded-xl p-4 text-left hover:scale-[1.02] transition-all duration-200 group"
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-2xl block group-hover:scale-110 transition-transform">{tool.icon}</span>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full border ${LEVEL_CLASS[tool.level] || LEVEL_CLASS['辅助']}`}>
                      {tool.level}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-white mt-3">{tool.label}</p>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
