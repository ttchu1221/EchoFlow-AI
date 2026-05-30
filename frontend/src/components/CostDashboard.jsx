import { useState, useEffect } from 'react';

const API = '/api/cost';

export default function CostDashboard() {
  const [summary, setSummary] = useState(null);
  const [budget, setBudget] = useState(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(30);

  const load = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const [sumRes, budRes] = await Promise.all([
        fetch(`${API}/summary?days=${days}`, { headers }),
        fetch(`${API}/budget`, { headers }),
      ]);
      const sumData = await sumRes.json();
      const budData = await budRes.json();
      if (sumData.code === 200) setSummary(sumData.data);
      if (budData.code === 200) setBudget(budData.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, [days]);

  const updateBudget = async (field, value) => {
    const newBudget = { ...budget, [field]: parseFloat(value) };
    setBudget(newBudget);
    await fetch(`${API}/budget`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(newBudget),
    });
  };

  if (loading && !summary) {
    return <div className="text-center py-12 text-txt-muted">加载中...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-txt-primary">💰 成本控制</h2>
        <div className="flex gap-2">
          {[7, 30, 90].map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium ${days === d ? 'bg-brand-500 text-white' : 'bg-panel-100 text-txt-muted'}`}>
              {d} 天
            </button>
          ))}
        </div>
      </div>

      {summary && (
        <>
          {/* 概览卡片 */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-panel-50/80 border border-panel-border rounded-xl p-4">
              <div className="text-xs text-txt-muted mb-1">今日消耗</div>
              <div className="text-2xl font-bold text-brand-400">¥{summary.today_cost_cny?.toFixed(2) || '0.00'}</div>
              {budget && (
                <div className="mt-2">
                  <div className="w-full h-1.5 bg-panel-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${summary.budget?.daily_usage_pct > 80 ? 'bg-red-500' : 'bg-brand-500'}`}
                      style={{ width: `${Math.min(summary.budget?.daily_usage_pct || 0, 100)}%` }}
                    />
                  </div>
                  <div className="text-xs text-txt-muted mt-1">{summary.budget?.daily_usage_pct || 0}% / 日预算 ¥{budget.daily_limit_cny}</div>
                </div>
              )}
            </div>
            <div className="bg-panel-50/80 border border-panel-border rounded-xl p-4">
              <div className="text-xs text-txt-muted mb-1">本月消耗</div>
              <div className="text-2xl font-bold text-green-400">¥{summary.month_cost_cny?.toFixed(2) || '0.00'}</div>
              {budget && (
                <div className="text-xs text-txt-muted mt-2">{summary.budget?.monthly_usage_pct || 0}% / 月预算 ¥{budget.monthly_limit_cny}</div>
              )}
            </div>
            <div className="bg-panel-50/80 border border-panel-border rounded-xl p-4">
              <div className="text-xs text-txt-muted mb-1">总调用次数</div>
              <div className="text-2xl font-bold text-blue-400">{summary.total_calls || 0}</div>
            </div>
            <div className="bg-panel-50/80 border border-panel-border rounded-xl p-4">
              <div className="text-xs text-txt-muted mb-1">总 Token 消耗</div>
              <div className="text-2xl font-bold text-purple-400">{(summary.total_tokens || 0).toLocaleString()}</div>
            </div>
          </div>

          {/* 按模型统计 */}
          <div className="bg-panel-50/80 border border-panel-border rounded-xl p-6">
            <h3 className="text-sm font-medium text-txt-secondary mb-4">按模型统计</h3>
            <div className="space-y-3">
              {Object.entries(summary.by_model || {}).map(([model, stats]) => (
                <div key={model} className="flex items-center gap-4">
                  <div className="w-40 text-sm text-txt-primary truncate">{model}</div>
                  <div className="flex-1 h-2 bg-panel-100 rounded-full overflow-hidden">
                    <div className="h-full bg-brand-500 rounded-full" style={{ width: `${Math.min((stats.cost_cny / (summary.total_cost_cny || 1)) * 100, 100)}%` }} />
                  </div>
                  <div className="w-24 text-right text-sm text-txt-muted">{stats.calls} 次</div>
                  <div className="w-20 text-right text-sm text-brand-400">¥{stats.cost_cny?.toFixed(2)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 按 Agent 统计 */}
          <div className="bg-panel-50/80 border border-panel-border rounded-xl p-6">
            <h3 className="text-sm font-medium text-txt-secondary mb-4">按 Agent 统计</h3>
            <div className="space-y-3">
              {Object.entries(summary.by_agent || {}).map(([agent, stats]) => (
                <div key={agent} className="flex items-center gap-4">
                  <div className="w-40 text-sm text-txt-primary truncate">{agent}</div>
                  <div className="flex-1 h-2 bg-panel-100 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500 rounded-full" style={{ width: `${Math.min((stats.cost_cny / (summary.total_cost_cny || 1)) * 100, 100)}%` }} />
                  </div>
                  <div className="w-24 text-right text-sm text-txt-muted">{stats.calls} 次</div>
                  <div className="w-20 text-right text-sm text-green-400">¥{stats.cost_cny?.toFixed(4)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 预算设置 */}
          {budget && (
            <div className="bg-panel-50/80 border border-panel-border rounded-xl p-6">
              <h3 className="text-sm font-medium text-txt-secondary mb-4">预算设置</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-txt-muted">每日预算 (¥)</label>
                  <input type="number" value={budget.daily_limit_cny}
                    onChange={e => updateBudget('daily_limit_cny', e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm" />
                </div>
                <div>
                  <label className="text-xs text-txt-muted">每月预算 (¥)</label>
                  <input type="number" value={budget.monthly_limit_cny}
                    onChange={e => updateBudget('monthly_limit_cny', e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm" />
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
