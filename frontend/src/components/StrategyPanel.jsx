import { useState } from 'react';
import { generateStrategy, getGrowthStats } from '../api/client';
import { withLLMProvider } from '../utils/llmProvider';
import DashboardChart, { NEON_COLORS } from './DashboardChart';
import StatsCard from './StatsCard';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

const STAGE_COLORS = {
  '冷启动': { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/30', neon: 'neon-blue' },
  '成长期': { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', neon: 'neon-green' },
  '瓶颈期': { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30', neon: 'neon-amber' },
  '成熟期': { bg: 'bg-purple-500/15', text: 'text-purple-400', border: 'border-purple-500/30', neon: 'neon-purple' },
};

export default function StrategyPanel() {
  const [form, setForm] = useState({
    growth_goal: '', niche: '', platform: 'xiaohongshu',
    current_followers: 0, content_count: 0, time_frame: '30d', creator_profile: '',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  const handleGenerate = async () => {
    if (!form.growth_goal.trim() || !form.niche.trim()) return;
    setLoading(true);
    try {
      const [data, statsData] = await Promise.all([generateStrategy(withLLMProvider(form)), getGrowthStats()]);
      setResult(data);
      setStats(statsData);
    } catch (e) { alert(e.message); } finally { setLoading(false); }
  };

  const update = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  /* ── 仪表盘：阶段评分 ─────────────────────────── */
  const gaugeOption = result?.creator_stage ? {
    series: [{
      type: 'gauge',
      startAngle: 210, endAngle: -30,
      min: 0, max: 100,
      radius: '90%',
      progress: { show: true, width: 14, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#22d3ee' }, { offset: 1, color: '#a78bfa' }] } } },
      axisLine: { lineStyle: { width: 14, color: [[1, 'rgba(56, 66, 86, 0.3)']] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: { show: false },
      title: { show: true, offsetCenter: [0, '70%'], fontSize: 14, color: '#e2e8f0' },
      detail: {
        valueAnimation: true, fontSize: 36, fontWeight: 'bold', offsetCenter: [0, '30%'],
        color: '#22d3ee', formatter: '{value}',
        textShadowColor: 'rgba(34, 211, 238, 0.3)', textShadowBlur: 20,
      },
      data: [{ value: result.creator_stage.score || 0, name: result.creator_stage.stage || '' }],
    }],
  } : null;

  /* ── 雷达图：内容方向 ─────────────────────────── */
  const radarOption = result?.content_directions ? {
    radar: {
      indicator: result.content_directions.slice(0, 6).map(d => ({
        name: d.direction?.slice(0, 8) || '', max: 100,
      })),
      shape: 'polygon',
      axisName: { color: '#94a3b8', fontSize: 11 },
      splitArea: { areaStyle: { color: ['rgba(34,211,238,0.02)', 'rgba(34,211,238,0.04)'] } },
      splitLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.4)' } },
      axisLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.4)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: result.content_directions.slice(0, 6).map(d => {
          const p = d.priority;
          return p === '高' ? 90 : p === '中' ? 65 : 40;
        }),
        name: '推荐强度',
        areaStyle: { color: 'rgba(34, 211, 238, 0.15)' },
        lineStyle: { color: '#22d3ee', width: 2 },
        itemStyle: { color: '#22d3ee' },
      }],
    }],
    tooltip: { trigger: 'item' },
  } : null;

  /* ── 里程碑时间线柱状图 ───────────────────────── */
  const milestoneOption = result?.growth_milestones ? {
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: result.growth_milestones.map(m => m.milestone?.slice(0, 8) || ''),
      axisLabel: { color: '#64748b', fontSize: 10, rotate: 15 },
    },
    yAxis: { type: 'value', show: false },
    series: [{
      type: 'bar',
      data: result.growth_milestones.map((m, i) => ({
        value: (i + 1) * 20,
        itemStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: NEON_COLORS[i % NEON_COLORS.length] }, { offset: 1, color: NEON_COLORS[i % NEON_COLORS.length] + '33' }] },
          borderRadius: [6, 6, 0, 0],
        },
      })),
      barWidth: 32,
      label: { show: true, position: 'top', color: '#94a3b8', fontSize: 10, formatter: (p) => result.growth_milestones[p.dataIndex]?.target_value || '' },
    }],
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const m = result.growth_milestones[params[0]?.dataIndex];
        return `<div style="font-weight:600;color:#e2e8f0">${m?.milestone}</div><div style="color:#94a3b8;font-size:12px;margin-top:4px">目标: ${m?.target_value}</div>`;
      },
    },
  } : null;

  const priorityColor = (p) => p === '高' ? 'tag-red' : p === '中' ? 'tag-amber' : 'tag-gray';

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-txt-bright flex items-center gap-3">
          <span className="w-1 h-6 rounded-full bg-gradient-to-b from-purple-400 to-brand-400" />
          策略智能体
        </h2>
        <p className="text-sm text-txt-secondary mt-1">系统核心大脑 — 制定从策略到发布的全局增长方案</p>
      </div>

      {/* 增长统计概览 */}
      {stats && stats.total > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          <StatsCard label="总内容数" value={stats.total} icon="📊" color="cyan" />
          <StatsCard label="爆款" value={stats.viral} icon="🔥" color="red" />
          <StatsCard label="良好" value={stats.good} icon="👍" color="green" />
          <StatsCard label="爆款率" value={stats.viral_rate} unit="%" icon="📈" color="amber" />
          <StatsCard label="成功率" value={stats.success_rate} unit="%" icon="🎯" color="blue" />
        </div>
      )}

      {/* 输入表单 */}
      <div className="card-glow p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">增长目标 *</label>
            <input className="input" placeholder="如：30天增长1万粉丝" value={form.growth_goal} onChange={(e) => update('growth_goal', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">领域/赛道 *</label>
            <input className="input" placeholder="如：AI科研、美妆、科技" value={form.niche} onChange={(e) => update('niche', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">目标平台</label>
            <select className="select" value={form.platform} onChange={(e) => update('platform', e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">目标时间</label>
            <select className="select" value={form.time_frame} onChange={(e) => update('time_frame', e.target.value)}>
              <option value="7d">7 天</option><option value="30d">30 天</option><option value="90d">90 天</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">当前粉丝数</label>
            <input type="number" className="input" value={form.current_followers} onChange={(e) => update('current_followers', parseInt(e.target.value) || 0)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">已发布内容数</label>
            <input type="number" className="input" value={form.content_count} onChange={(e) => update('content_count', parseInt(e.target.value) || 0)} />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-txt-secondary mb-1.5">创作者画像（可选）</label>
          <textarea className="input min-h-[60px]" placeholder="描述你的账号定位、内容风格、目标受众..." value={form.creator_profile} onChange={(e) => update('creator_profile', e.target.value)} />
        </div>
        <button className="btn-primary w-full sm:w-auto" onClick={handleGenerate} disabled={loading || !form.growth_goal.trim() || !form.niche.trim()}>
          {loading ? '🧠 策略分析中...' : '🧠 生成增长策略'}
        </button>
      </div>

      {loading && (
        <div className="card p-8 text-center">
          <div className="inline-block w-8 h-8 border-4 border-brand-500/30 border-t-brand-400 rounded-full animate-spin mb-3" />
          <p className="text-txt-secondary">策略智能体正在分析中，请稍候...</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-5 animate-slide-up">
          {/* 仪表盘 + 雷达图 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {gaugeOption && (
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-txt-primary mb-2 flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-brand-400" />
                  创作者阶段评估
                </h3>
                <DashboardChart option={gaugeOption} height={260} />
                <p className="text-sm text-txt-secondary text-center px-4 -mt-2">{result.creator_stage?.description}</p>
              </div>
            )}
            {radarOption && (
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-txt-primary mb-2 flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-purple-400" />
                  内容方向推荐强度
                </h3>
                <DashboardChart option={radarOption} height={300} />
              </div>
            )}
          </div>

          {/* 内容方向详情 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-txt-primary mb-4">🎯 内容方向建议</h3>
            <div className="space-y-3">
              {(result.content_directions || []).map((d, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-panel-100/50 border border-panel-border/50">
                  <span className="text-lg font-bold text-brand-400">{i + 1}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-txt-bright">{d.direction}</span>
                      <span className={priorityColor(d.priority)}>{d.priority}</span>
                    </div>
                    <p className="text-sm text-txt-secondary">{d.description}</p>
                    {d.expected_impact && <p className="text-xs text-emerald-400 mt-1">💡 {d.expected_impact}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 发布策略 */}
          {result.posting_strategy && Object.keys(result.posting_strategy).length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-txt-primary mb-4">📅 发布策略</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {result.posting_strategy.frequency && (
                  <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                    <div className="text-sm font-medium text-blue-400">发布频率</div>
                    <div className="text-lg font-bold text-blue-300">{result.posting_strategy.frequency}</div>
                  </div>
                )}
                {result.posting_strategy.best_times && (
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="text-sm font-medium text-emerald-400">最佳时段</div>
                    <div className="text-lg font-bold text-emerald-300">
                      {Array.isArray(result.posting_strategy.best_times) ? result.posting_strategy.best_times.join('、') : result.posting_strategy.best_times}
                    </div>
                  </div>
                )}
                {result.posting_strategy.content_rhythm && (
                  <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 sm:col-span-2">
                    <div className="text-sm font-medium text-purple-400">内容节奏</div>
                    <div className="text-txt-primary">{result.posting_strategy.content_rhythm}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 钩子策略 & 互动策略 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-txt-primary mb-4">🎣 钩子策略</h3>
              <ul className="space-y-2">
                {(result.hook_strategies || []).map((h, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-txt-secondary">
                    <span className="text-neon-amber mt-0.5">▸</span> {h}
                  </li>
                ))}
              </ul>
            </div>
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-txt-primary mb-4">💬 互动策略</h3>
              <ul className="space-y-2">
                {(result.engagement_tactics || []).map((t, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-txt-secondary">
                    <span className="text-neon-green mt-0.5">▸</span> {t}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* 增长里程碑 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-txt-primary mb-4">🏆 增长里程碑</h3>
            {milestoneOption && <DashboardChart option={milestoneOption} height={200} className="mb-4" />}
            <div className="space-y-4">
              {(result.growth_milestones || []).map((m, i) => (
                <div key={i} className="relative pl-6 border-l-2 border-brand-500/30">
                  <div className="absolute -left-2 top-0 w-4 h-4 rounded-full bg-brand-500 shadow-neon-cyan" />
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-txt-bright">{m.milestone}</span>
                    <span className="tag-cyan">{m.target_value}</span>
                    {m.deadline && <span className="text-xs text-txt-muted">⏱ {m.deadline}</span>}
                  </div>
                  {m.action_items?.length > 0 && (
                    <ul className="mt-1 space-y-1">
                      {m.action_items.map((a, j) => <li key={j} className="text-sm text-txt-secondary">• {a}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 风险提示 */}
          {result.risk_alerts?.length > 0 && (
            <div className="card p-6 border-l-4 border-amber-500/50 bg-amber-500/5">
              <h3 className="text-lg font-semibold text-amber-400 mb-3">⚠️ 风险提示</h3>
              <ul className="space-y-2">
                {result.risk_alerts.map((r, i) => <li key={i} className="text-sm text-amber-300/80">• {r}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
