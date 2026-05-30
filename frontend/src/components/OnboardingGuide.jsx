import { useState, useEffect } from 'react';

const API = '/api/onboarding';

export default function OnboardingGuide({ onNavigate }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const load = async () => {
    setLoading(true);
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
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const completeStep = async (stepId) => {
    await fetch(`${API}/complete/${stepId}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    });
    load();
  };

  const dismiss = async () => {
    await fetch(`${API}/dismiss`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    });
    setDismissed(true);
  };

  if (loading || dismissed || !status || status.all_completed) return null;

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
          <div className="text-sm text-brand-400 font-medium">{status.progress_pct}%</div>
          <div className="w-32 h-2 bg-panel-100 rounded-full overflow-hidden">
            <div className="h-full bg-brand-500 rounded-full transition-all duration-500"
              style={{ width: `${status.progress_pct}%` }} />
          </div>
          <button onClick={dismiss} className="text-txt-muted hover:text-txt-primary text-sm">跳过</button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {status.steps?.map(step => {
          const isCompleted = status.completed_steps?.includes(step.id);
          const isNext = status.next_step?.id === step.id;
          return (
            <div
              key={step.id}
              className={`relative p-4 rounded-xl border transition-all cursor-pointer ${
                isCompleted
                  ? 'bg-green-500/5 border-green-500/20'
                  : isNext
                    ? 'bg-brand-500/10 border-brand-500/40 ring-1 ring-brand-500/20'
                    : 'bg-panel-50/50 border-panel-border hover:border-brand-500/30'
              }`}
              onClick={() => {
                if (isNext && step.route) {
                  onNavigate?.(step.route);
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
              {isNext && (
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
