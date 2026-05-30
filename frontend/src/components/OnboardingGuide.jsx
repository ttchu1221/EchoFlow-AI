import { useState, useEffect } from 'react';

const API = '/api/onboarding';

const DEFAULT_STEPS = [
  { id: 'welcome', title: '了解系统', description: '熟悉 EchoFlow AI 的核心功能', action: '开始探索', route: '/trends' },
  { id: 'view_trends', title: '查看趋势', description: '了解当前热门话题和趋势', action: '查看趋势', route: '/trends' },
  { id: 'first_pipeline', title: '首次创作', description: '使用全流程生成第一篇内容', action: '去创作', route: '/pipeline' },
  { id: 'bind_account', title: '绑定账号', description: '连接你的社交媒体账号', action: '去绑定', route: '/accounts' },
  { id: 'setup_schedule', title: '设置定时', description: '配置自动化发布计划', action: '去设置', route: '/schedules' },
  { id: 'invite_team', title: '邀请团队', description: '邀请团队成员协作', action: '去邀请', route: '/team' },
];

export default function OnboardingGuide({ onNavigate }) {
  const [status, setStatus] = useState(null);
  const [dismissed, setDismissed] = useState(false);

  const load = async () => {
    try {
      const res = await fetch(`${API}/status`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const data = await res.json();
      if (data.code === 200) {
        setStatus(data.data);
        if (data.data.dismissed || data.data.all_completed) {
          setDismissed(true);
        }
      } else {
        // API 返回错误，使用默认步骤
        setStatus({ steps: DEFAULT_STEPS, completed_steps: [], progress_pct: 0, next_step: DEFAULT_STEPS[0] });
      }
    } catch (e) {
      // API 不可用，使用默认步骤
      setStatus({ steps: DEFAULT_STEPS, completed_steps: [], progress_pct: 0, next_step: DEFAULT_STEPS[0] });
    }
  };

  useEffect(() => { load(); }, []);

  const completeStep = async (stepId) => {
    // 先导航
    const step = status?.steps?.find(s => s.id === stepId);
    if (step?.route) {
      onNavigate?.(step.route);
    }

    // 再更新状态（忽略错误）
    try {
      await fetch(`${API}/complete/${stepId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
    } catch (e) {}

    // 更新本地状态
    setStatus(prev => {
      if (!prev) return prev;
      const completed = [...(prev.completed_steps || []), stepId];
      const allDone = completed.length >= (prev.steps?.length || 6);
      return {
        ...prev,
        completed_steps: completed,
        progress_pct: Math.round((completed.length / (prev.steps?.length || 6)) * 100),
        all_completed: allDone,
      };
    });
  };

  const dismiss = () => {
    setDismissed(true);
    fetch(`${API}/dismiss`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    }).catch(() => {});
  };

  if (dismissed || status?.all_completed) return null;

  const steps = status?.steps || DEFAULT_STEPS;
  const completedSteps = status?.completed_steps || [];
  const progressPct = status?.progress_pct ?? Math.round((completedSteps.length / steps.length) * 100);
  const nextStep = status?.next_step || steps.find(s => !completedSteps.includes(s.id));

  const stepIcons = {
    welcome: '👋', bind_account: '🔗', first_pipeline: '⚡',
    view_trends: '📊', setup_schedule: '⏰', invite_team: '👥',
  };

  return (
    <div className="bg-gradient-to-r from-brand-500/10 to-brand-700/10 border border-brand-500/30 rounded-2xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-txt-primary">🚀 快速上手</h3>
          <p className="text-sm text-txt-muted">完成以下步骤，快速掌握 EchoFlow AI</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-brand-400 font-medium">{progressPct}%</div>
          <div className="w-32 h-2 bg-panel-100 rounded-full overflow-hidden">
            <div className="h-full bg-brand-500 rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%` }} />
          </div>
          <button
            onClick={dismiss}
            className="text-txt-muted hover:text-txt-primary text-sm px-2 py-1 rounded hover:bg-panel-100 transition-colors"
          >
            跳过
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {steps.map(step => {
          const isCompleted = completedSteps.includes(step.id);
          const isNext = nextStep?.id === step.id;
          return (
            <div
              key={step.id}
              className={`relative p-4 rounded-xl border transition-all ${
                isCompleted
                  ? 'bg-green-500/5 border-green-500/20'
                  : isNext
                    ? 'bg-brand-500/10 border-brand-500/40 ring-1 ring-brand-500/20 cursor-pointer'
                    : 'bg-panel-50/50 border-panel-border hover:border-brand-500/30 cursor-pointer'
              }`}
              onClick={() => {
                if (!isCompleted && step.route) {
                  completeStep(step.id);
                }
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{stepIcons[step.id] || '📌'}</span>
                <span className={`text-sm font-medium ${isCompleted ? 'text-green-400' : 'text-txt-primary'}`}>
                  {step.title}
                </span>
                {isCompleted && <span className="text-green-400">✓</span>}
              </div>
              <p className="text-xs text-txt-muted">{step.description}</p>
              {!isCompleted && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    completeStep(step.id);
                  }}
                  className="mt-3 px-3 py-1.5 bg-brand-500 text-white rounded-lg text-xs font-medium hover:bg-brand-600 transition-all"
                >
                  {step.action}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
