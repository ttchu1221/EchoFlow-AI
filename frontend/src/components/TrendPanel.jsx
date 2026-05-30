import { useState } from 'react';
import { analyzeTrends } from '../api/client';
import { withLLMProvider } from '../utils/llmProvider';
import DashboardChart, { NEON_COLORS } from './DashboardChart';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

export default function TrendPanel() {
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('douyin');
  const [timeRange, setTimeRange] = useState('7d');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const data = await analyzeTrends(withLLMProvider({ topic, platform, time_range: timeRange }));
      setResult(data);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  /* ── 热度条形图 ────────────────────────────────── */
  const heatBarOption = result?.trending_topics ? {
    grid: { left: 140, right: 60, top: 10, bottom: 30 },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category',
      data: result.trending_topics.map(t => t.topic).reverse(),
      axisLabel: { color: '#94a3b8', fontSize: 11, width: 120, overflow: 'truncate' },
      axisLine: { show: false }, axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: result.trending_topics.map((t, i) => ({
        value: t.heat_score || 0,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: NEON_COLORS[i % NEON_COLORS.length] + '22' }, { offset: 1, color: NEON_COLORS[i % NEON_COLORS.length] }] },
        },
      })).reverse(),
      barWidth: 18,
      label: {
        show: true, position: 'right',
        formatter: (p) => {
          const t = result.trending_topics[result.trending_topics.length - 1 - p.dataIndex];
          return `{score|${p.value}} {dir|${t?.trend_direction === '上升' ? '↑' : t?.trend_direction === '下降' ? '↓' : '→'}}`;
        },
        rich: { score: { color: '#e2e8f0', fontSize: 12, fontWeight: 'bold' }, dir: { fontSize: 14 } },
      },
    }],
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  } : null;

  /* ── 趋势方向饼图 ──────────────────────────────── */
  const directionPieOption = result?.trending_topics ? {
    series: [{
      type: 'pie', radius: ['50%', '72%'], center: ['50%', '50%'],
      data: (() => {
        const counts = { '上升': 0, '下降': 0, '平稳': 0 };
        result.trending_topics.forEach(t => { counts[t.trend_direction] = (counts[t.trend_direction] || 0) + 1; });
        return [
          counts['上升'] > 0 && { value: counts['上升'], name: '上升', itemStyle: { color: '#34d399' } },
          counts['下降'] > 0 && { value: counts['下降'], name: '下降', itemStyle: { color: '#f87171' } },
          counts['平稳'] > 0 && { value: counts['平稳'], name: '平稳', itemStyle: { color: '#64748b' } },
        ].filter(Boolean);
      })(),
      label: { show: true, color: '#94a3b8', fontSize: 12, formatter: '{b}\n{d}%' },
      emphasis: { label: { fontSize: 14, fontWeight: 'bold' } },
      itemStyle: { borderColor: '#0d1117', borderWidth: 3 },
    }],
    tooltip: { trigger: 'item' },
  } : null;

  /* ── 关键词关联网络（散点图模拟）──────────────── */
  const keywordScatterOption = result?.trending_topics ? {
    grid: { left: 20, right: 20, top: 20, bottom: 20 },
    xAxis: { type: 'value', show: false, min: 0, max: 100 },
    yAxis: { type: 'value', show: false, min: 0, max: 100 },
    series: [{
      type: 'scatter',
      symbolSize: (val) => Math.max(20, val[2] * 0.8),
      data: result.trending_topics.flatMap((t, i) => {
        const cx = 20 + (i % 3) * 30;
        const cy = 30 + Math.floor(i / 3) * 35;
        return [
          [cx, cy, (t.heat_score || 50) * 0.5, t.topic, NEON_COLORS[i % NEON_COLORS.length]],
          ...(t.related_keywords || []).slice(0, 3).map((k, j) => {
            const angle = (j / 3) * Math.PI * 2;
            return [cx + Math.cos(angle) * 18, cy + Math.sin(angle) * 18, 15, k, NEON_COLORS[(i + j + 1) % NEON_COLORS.length]];
          }),
        ];
      }),
      itemStyle: {
        color: (p) => p.data[4] + '33',
        borderColor: (p) => p.data[4],
        borderWidth: 1.5,
      },
      label: {
        show: true, position: 'inside',
        formatter: (p) => p.data[3],
        color: '#e2e8f0', fontSize: 10,
      },
    }],
    tooltip: {
      trigger: 'item',
      formatter: (p) => `<span style="color:${p.data[4]}">${p.data[3]}</span>`,
    },
  } : null;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-txt-bright flex items-center gap-3">
          <span className="w-1 h-6 rounded-full bg-gradient-to-b from-blue-400 to-purple-600" />
          趋势分析
        </h2>
        <p className="text-sm text-txt-secondary mt-1">结合实时数据与 AI 分析，发现内容趋势与爆款模式</p>
      </div>

      <div className="card-glow p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">目标平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">时间范围</label>
            <select className="select" value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
              <option value="1d">近 24 小时</option>
              <option value="7d">近 7 天</option>
              <option value="30d">近 30 天</option>
            </select>
          </div>
          <div className="flex items-end">
            <button className="btn-primary w-full" onClick={handleAnalyze} disabled={loading || !topic.trim()}>
              {loading ? <><span className="animate-spin">⏳</span> 分析中...</> : '📊 开始分析'}
            </button>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-txt-secondary mb-1.5">分析领域</label>
          <input type="text" className="input" placeholder="例如：护肤、健身、编程教学..."
            value={topic} onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()} />
        </div>
      </div>

      {loading && (
        <div className="card p-8 text-center">
          <div className="inline-block w-8 h-8 border-4 border-brand-500/30 border-t-brand-400 rounded-full animate-spin mb-3" />
          <p className="text-txt-secondary">趋势分析引擎运行中...</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-6 animate-slide-up">
          {/* 图表区 */}
          {heatBarOption && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2 card p-4">
                <h3 className="text-sm font-semibold text-txt-primary mb-2 flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-brand-400" />
                  热门话题热度
                </h3>
                <DashboardChart option={heatBarOption} height={Math.max(280, (result.trending_topics?.length || 3) * 50)} />
              </div>
              <div className="card p-4 space-y-4">
                <h3 className="text-sm font-semibold text-txt-primary flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-purple-400" />
                  趋势方向分布
                </h3>
                <DashboardChart option={directionPieOption} height={200} />
                <h3 className="text-sm font-semibold text-txt-primary flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-emerald-400" />
                  关键词关联
                </h3>
                <DashboardChart option={keywordScatterOption} height={200} />
              </div>
            </div>
          )}

          {/* 热门话题详情 */}
          <div>
            <h3 className="text-lg font-semibold text-txt-primary mb-3">🔥 热门话题详情</h3>
            <div className="grid gap-3">
              {result.trending_topics?.map((t, i) => (
                <div key={i} className="card p-5">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h4 className="font-semibold text-txt-bright flex-1">{t.topic}</h4>
                    <div className="flex gap-2 flex-shrink-0">
                      <span className="tag-cyan">热度 {t.heat_score}</span>
                      <span className={t.trend_direction === '上升' ? 'tag-green' : t.trend_direction === '下降' ? 'tag-red' : 'tag-gray'}>
                        {t.trend_direction === '上升' ? '📈' : t.trend_direction === '下降' ? '📉' : '➡️'} {t.trend_direction}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-txt-secondary mb-3">{t.reason}</p>
                  {t.related_keywords?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {t.related_keywords.map((k, j) => <span key={j} className="tag-gray">#{k}</span>)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 爆款模式 */}
          <div>
            <h3 className="text-lg font-semibold text-txt-primary mb-3">💡 爆款内容模式</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {result.viral_patterns?.map((p, i) => (
                <div key={i} className="card-glow p-5">
                  <h4 className="font-semibold text-txt-bright mb-2">{p.pattern_name}</h4>
                  <p className="text-sm text-txt-secondary mb-3">{p.description}</p>
                  <div className="space-y-1 mb-3">
                    {p.examples?.map((e, j) => <p key={j} className="text-xs text-txt-muted">• {e}</p>)}
                  </div>
                  <span className="tag-purple">{p.applicability}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 受众洞察 */}
          <div>
            <h3 className="text-lg font-semibold text-txt-primary mb-3">👥 受众洞察</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.audience_insights?.map((a, i) => (
                <div key={i} className="card p-5">
                  <h4 className="font-semibold text-txt-bright mb-3">{a.segment}</h4>
                  <div className="space-y-2">
                    <div>
                      <span className="text-xs font-medium text-txt-muted">兴趣</span>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {a.interests?.map((t, j) => <span key={j} className="tag-cyan">{t}</span>)}
                      </div>
                    </div>
                    <div>
                      <span className="text-xs font-medium text-txt-muted">痛点</span>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {a.pain_points?.map((t, j) => <span key={j} className="tag-red">{t}</span>)}
                      </div>
                    </div>
                    <p className="text-sm text-txt-secondary mt-2">{a.content_preference}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
