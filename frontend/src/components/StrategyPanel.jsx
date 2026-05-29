import { useState } from 'react';
import { generateStrategy, getGrowthStats } from '../api/client';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

const STAGE_COLORS = {
  '冷启动': 'bg-blue-100 text-blue-700',
  '成长期': 'bg-emerald-100 text-emerald-700',
  '瓶颈期': 'bg-amber-100 text-amber-700',
  '成熟期': 'bg-purple-100 text-purple-700',
};

export default function StrategyPanel() {
  const [form, setForm] = useState({
    growth_goal: '',
    niche: '',
    platform: 'xiaohongshu',
    current_followers: 0,
    content_count: 0,
    time_frame: '30d',
    creator_profile: '',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  const handleGenerate = async () => {
    if (!form.growth_goal.trim() || !form.niche.trim()) return;
    setLoading(true);
    try {
      const [data, statsData] = await Promise.all([
        generateStrategy(form),
        getGrowthStats(),
      ]);
      setResult(data);
      setStats(statsData);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const update = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  const priorityColor = (p) => {
    if (p === '高') return 'tag-red';
    if (p === '中') return 'tag-amber';
    return 'tag-gray';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">🧠 策略智能体</h2>
        <p className="text-sm text-gray-500 mt-1">系统核心大脑 — 制定从策略到发布的全局增长方案</p>
      </div>

      {/* 增长统计概览 */}
      {stats && stats.total > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="card-flat p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-xs text-gray-500 mt-1">总内容数</div>
          </div>
          <div className="card-flat p-4 text-center">
            <div className="text-2xl font-bold text-red-500">{stats.viral}</div>
            <div className="text-xs text-gray-500 mt-1">🔥 爆款</div>
          </div>
          <div className="card-flat p-4 text-center">
            <div className="text-2xl font-bold text-emerald-500">{stats.good}</div>
            <div className="text-xs text-gray-500 mt-1">👍 良好</div>
          </div>
          <div className="card-flat p-4 text-center">
            <div className="text-2xl font-bold text-amber-500">{stats.viral_rate}%</div>
            <div className="text-xs text-gray-500 mt-1">爆款率</div>
          </div>
          <div className="card-flat p-4 text-center">
            <div className="text-2xl font-bold text-brand-600">{stats.success_rate}%</div>
            <div className="text-xs text-gray-500 mt-1">成功率</div>
          </div>
        </div>
      )}

      {/* 输入表单 */}
      <div className="card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">增长目标 *</label>
            <input
              className="input"
              placeholder="如：30天增长1万粉丝"
              value={form.growth_goal}
              onChange={(e) => update('growth_goal', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">领域/赛道 *</label>
            <input
              className="input"
              placeholder="如：AI科研、美妆、科技"
              value={form.niche}
              onChange={(e) => update('niche', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">目标平台</label>
            <select className="select" value={form.platform} onChange={(e) => update('platform', e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">目标时间</label>
            <select className="select" value={form.time_frame} onChange={(e) => update('time_frame', e.target.value)}>
              <option value="7d">7 天</option>
              <option value="30d">30 天</option>
              <option value="90d">90 天</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">当前粉丝数</label>
            <input
              type="number"
              className="input"
              value={form.current_followers}
              onChange={(e) => update('current_followers', parseInt(e.target.value) || 0)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">已发布内容数</label>
            <input
              type="number"
              className="input"
              value={form.content_count}
              onChange={(e) => update('content_count', parseInt(e.target.value) || 0)}
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">创作者画像（可选）</label>
          <textarea
            className="input min-h-[60px]"
            placeholder="描述你的账号定位、内容风格、目标受众..."
            value={form.creator_profile}
            onChange={(e) => update('creator_profile', e.target.value)}
          />
        </div>
        <button
          className="btn-primary w-full sm:w-auto"
          onClick={handleGenerate}
          disabled={loading || !form.growth_goal.trim() || !form.niche.trim()}
        >
          {loading ? '🧠 策略分析中...' : '🧠 生成增长策略'}
        </button>
      </div>

      {/* 加载状态 */}
      {loading && (
        <div className="card p-8 text-center">
          <div className="inline-block w-8 h-8 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mb-3" />
          <p className="text-gray-500">策略智能体正在分析中，请稍候...</p>
        </div>
      )}

      {/* 结果展示 */}
      {result && !loading && (
        <div className="space-y-5 animate-fade-in">
          {/* 创作者阶段评估 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 创作者阶段评估</h3>
            <div className="flex items-center gap-4 mb-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${STAGE_COLORS[result.creator_stage?.stage] || 'bg-gray-100 text-gray-700'}`}>
                {result.creator_stage?.stage || '未知'}
              </span>
              <div className="flex-1">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>阶段评分</span>
                  <span>{result.creator_stage?.score || 0}/100</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-brand-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${result.creator_stage?.score || 0}%` }}
                  />
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-600">{result.creator_stage?.description}</p>
          </div>

          {/* 内容方向 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 内容方向建议</h3>
            <div className="space-y-3">
              {(result.content_directions || []).map((d, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50">
                  <span className="text-lg font-bold text-brand-500">{i + 1}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900">{d.direction}</span>
                      <span className={priorityColor(d.priority)}>{d.priority}</span>
                    </div>
                    <p className="text-sm text-gray-600">{d.description}</p>
                    {d.expected_impact && (
                      <p className="text-xs text-emerald-600 mt-1">💡 {d.expected_impact}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 发布策略 */}
          {result.posting_strategy && Object.keys(result.posting_strategy).length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📅 发布策略</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {result.posting_strategy.frequency && (
                  <div className="p-3 rounded-lg bg-blue-50">
                    <div className="text-sm font-medium text-blue-700">发布频率</div>
                    <div className="text-lg font-bold text-blue-900">{result.posting_strategy.frequency}</div>
                  </div>
                )}
                {result.posting_strategy.best_times && (
                  <div className="p-3 rounded-lg bg-emerald-50">
                    <div className="text-sm font-medium text-emerald-700">最佳时段</div>
                    <div className="text-lg font-bold text-emerald-900">
                      {Array.isArray(result.posting_strategy.best_times) ? result.posting_strategy.best_times.join('、') : result.posting_strategy.best_times}
                    </div>
                  </div>
                )}
                {result.posting_strategy.content_rhythm && (
                  <div className="p-3 rounded-lg bg-purple-50 sm:col-span-2">
                    <div className="text-sm font-medium text-purple-700">内容节奏</div>
                    <div className="text-gray-900">{result.posting_strategy.content_rhythm}</div>
                  </div>
                )}
              </div>
              {result.posting_strategy.notes && (
                <p className="text-sm text-gray-500 mt-3">⚠️ {result.posting_strategy.notes}</p>
              )}
            </div>
          )}

          {/* 钩子策略 & 互动策略 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🎣 钩子策略</h3>
              <ul className="space-y-2">
                {(result.hook_strategies || []).map((h, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="text-amber-500 mt-0.5">▸</span>
                    {h}
                  </li>
                ))}
              </ul>
            </div>
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">💬 互动策略</h3>
              <ul className="space-y-2">
                {(result.engagement_tactics || []).map((t, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="text-emerald-500 mt-0.5">▸</span>
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* 增长里程碑 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🏆 增长里程碑</h3>
            <div className="space-y-4">
              {(result.growth_milestones || []).map((m, i) => (
                <div key={i} className="relative pl-6 border-l-2 border-brand-300">
                  <div className="absolute -left-2 top-0 w-4 h-4 bg-brand-500 rounded-full" />
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-900">{m.milestone}</span>
                    <span className="tag-blue">{m.target_value}</span>
                    {m.deadline && <span className="text-xs text-gray-500">⏱ {m.deadline}</span>}
                  </div>
                  {m.action_items && m.action_items.length > 0 && (
                    <ul className="mt-1 space-y-1">
                      {m.action_items.map((a, j) => (
                        <li key={j} className="text-sm text-gray-600">• {a}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 风险提示 */}
          {result.risk_alerts && result.risk_alerts.length > 0 && (
            <div className="card p-6 border-l-4 border-amber-400 bg-amber-50">
              <h3 className="text-lg font-semibold text-amber-800 mb-3">⚠️ 风险提示</h3>
              <ul className="space-y-2">
                {result.risk_alerts.map((r, i) => (
                  <li key={i} className="text-sm text-amber-700">• {r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
