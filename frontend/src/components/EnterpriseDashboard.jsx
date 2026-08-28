import { useState, useEffect } from 'react';
import { getEnterpriseDashboard } from '../api/client';

const KPI_CARDS = [
  { key: 'gmv', icon: '💰', color: 'from-emerald-500 to-emerald-600', glow: 'shadow-[0_0_20px_rgba(16,185,129,0.3)]' },
  { key: 'roi', icon: '📈', color: 'from-cyan-500 to-cyan-600', glow: 'shadow-[0_0_20px_rgba(34,211,238,0.3)]' },
  { key: 'orders', icon: '📦', color: 'from-blue-500 to-blue-600', glow: 'shadow-[0_0_20px_rgba(59,130,246,0.3)]' },
  { key: 'ad_spend', icon: '📊', color: 'from-amber-500 to-amber-600', glow: 'shadow-[0_0_20px_rgba(245,158,11,0.3)]' },
  { key: 'content_published', icon: '✍️', color: 'from-purple-500 to-purple-600', glow: 'shadow-[0_0_20px_rgba(168,85,247,0.3)]' },
  { key: 'agent_tasks', icon: '🤖', color: 'from-pink-500 to-pink-600', glow: 'shadow-[0_0_20px_rgba(236,72,153,0.3)]' },
];

function formatValue(val, unit) {
  if (typeof val !== 'number') return val;
  if (unit === '¥') return `¥${val.toLocaleString()}`;
  return val.toLocaleString();
}

export default function EnterpriseDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const result = await getEnterpriseDashboard();
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-12 h-12 border-4 border-brand-500/30 border-t-brand-400 rounded-full animate-spin mb-4" />
          <p className="text-txt-secondary">加载企业驾驶舱...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="card p-8 text-center max-w-md">
          <div className="text-4xl mb-4">⚠️</div>
          <h3 className="text-xl font-bold text-txt-primary mb-2">加载失败</h3>
          <p className="text-txt-secondary mb-4">{error}</p>
          <button onClick={loadDashboard} className="btn-primary">重试</button>
        </div>
      </div>
    );
  }

  const { kpis, ai_suggestions, agent_status, gmv_trend, platform_distribution, recent_activities } = data;

  return (
    <div className="dashboard-container min-h-screen p-6">
      {/* 顶部标题 */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white dashboard-glow-text">运营工作台</h1>
            <p className="text-txt-secondary mt-1">围绕 GMV、内容效率、竞品异动和执行任务做每日运营判断</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="tag-green animate-pulse">● 实时同步</span>
            <button onClick={loadDashboard} className="btn-ghost text-sm">
              🔄 刷新
            </button>
          </div>
        </div>
      </div>

      {/* KPI 卡片网格 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {KPI_CARDS.map(({ key, icon, color, glow }) => {
          const kpi = kpis[key];
          if (!kpi) return null;
          return (
            <div key={key} className={`dashboard-kpi-card relative rounded-2xl p-5 ${glow} hover:scale-[1.02] transition-all duration-300`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{icon}</span>
                {kpi.change && (
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    kpi.change.startsWith('+') ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {kpi.change}
                  </span>
                )}
              </div>
              <div className={`text-2xl font-bold bg-gradient-to-r ${color} bg-clip-text text-transparent`}>
                {formatValue(kpi.value, kpi.unit)}
              </div>
              <div className="text-xs text-txt-muted mt-1">{kpi.label}</div>
            </div>
          );
        })}
      </div>

      {/* 主内容区：左右布局 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* GMV 趋势图 */}
        <div className="lg:col-span-2 dashboard-panel rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">📈 GMV 7日趋势</h3>
          <div className="flex items-end gap-3 h-48">
            {gmv_trend.map((item, i) => {
              const maxVal = Math.max(...gmv_trend.map(d => d.value));
              const height = (item.value / maxVal) * 100;
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-2">
                  <span className="text-xs text-txt-muted">¥{(item.value / 1000).toFixed(0)}k</span>
                  <div
                    className="w-full rounded-t-lg bg-gradient-to-t from-brand-600 to-brand-400 transition-all duration-500 hover:from-brand-500 hover:to-brand-300"
                    style={{ height: `${height}%`, minHeight: '20px' }}
                  />
                  <span className="text-xs text-txt-muted">{item.date}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* 平台分布 */}
        <div className="dashboard-panel rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">🌐 平台分布</h3>
          <div className="space-y-4">
            {platform_distribution.map((p) => (
              <div key={p.platform}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-txt-secondary">{p.platform}</span>
                  <span className="text-white font-medium">{p.value}%</span>
                </div>
                <div className="h-2 bg-panel-200 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-1000"
                    style={{ width: `${p.value}%`, backgroundColor: p.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 下半部分：三列 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI 建议 */}
        <div className="dashboard-panel rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">今日运营建议</h3>
          <div className="space-y-3">
            {ai_suggestions.map((s) => (
              <div key={s.id} className="flex items-start gap-3 p-3 rounded-xl bg-panel-100/50 hover:bg-panel-100 transition-colors">
                <span className={`w-2 h-2 mt-2 rounded-full flex-shrink-0 ${
                  s.priority === 'high' ? 'bg-red-400' : s.priority === 'medium' ? 'bg-amber-400' : 'bg-emerald-400'
                }`} />
                <div>
                  <p className="text-sm text-txt-primary">{s.text}</p>
                  <span className="text-xs text-txt-muted mt-1 inline-block">来源：{s.agent}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Agent 状态 */}
        <div className="dashboard-panel rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">任务执行状态</h3>
          <div className="space-y-3">
            {agent_status.map((a) => (
              <div key={a.id} className="flex items-center gap-3 p-3 rounded-xl bg-panel-100/50">
                <span className="text-xl">{a.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{a.name}</p>
                  <p className="text-xs text-txt-muted">{a.tasks_today} 个任务今日</p>
                </div>
                <span className={`w-2 h-2 rounded-full ${a.status === 'active' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
              </div>
            ))}
          </div>
        </div>

        {/* 最近活动 */}
        <div className="dashboard-panel rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">最近运营动作</h3>
          <div className="space-y-3">
            {recent_activities.map((a, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-panel-100/50">
                <span className={`w-2 h-2 mt-2 rounded-full flex-shrink-0 ${
                  a.status === 'done' ? 'bg-emerald-400' : a.status === 'warning' ? 'bg-amber-400' : 'bg-red-400'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-txt-primary truncate">{a.action}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-txt-muted">{a.time}</span>
                    <span className="text-xs text-brand-400">来源：{a.agent}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
