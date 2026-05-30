import { useState } from 'react';
import { analyzePerformance } from '../api/client';
import { withLLMProvider } from '../utils/llmProvider';
import DashboardChart, { NEON_COLORS } from './DashboardChart';
import StatsCard from './StatsCard';

export default function AnalyticsPanel() {
  const [contentTitle, setContentTitle] = useState('');
  const [views, setViews] = useState('');
  const [likes, setLikes] = useState('');
  const [comments, setComments] = useState('');
  const [shares, setShares] = useState('');
  const [platform, setPlatform] = useState('xiaohongshu');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!contentTitle.trim()) return;
    setLoading(true);
    try {
      const data = await analyzePerformance(withLLMProvider({
        content_title: contentTitle,
        metrics: { views: parseInt(views) || 0, likes: parseInt(likes) || 0, comments: parseInt(comments) || 0, shares: parseInt(shares) || 0 },
        platform,
      }));
      setResult(data);
    } catch (e) { alert(e.message); } finally { setLoading(false); }
  };

  /* ── 互动指标环形图 ────────────────────────────── */
  const ringOption = result?.metrics ? {
    series: [{
      type: 'pie', radius: ['52%', '72%'], center: ['50%', '50%'],
      data: [
        { value: parseFloat(result.metrics.engagement_rate) || 0, name: '互动率', itemStyle: { color: '#22d3ee' } },
        { value: parseFloat(result.metrics.like_rate) || 0, name: '点赞率', itemStyle: { color: '#3b82f6' } },
        { value: parseFloat(result.metrics.comment_rate) || 0, name: '评论率', itemStyle: { color: '#a78bfa' } },
        { value: parseFloat(result.metrics.share_rate) || 0, name: '分享率', itemStyle: { color: '#fbbf24' } },
      ],
      label: {
        show: true, position: 'outside',
        formatter: '{b}\n{d}%',
        color: '#94a3b8', fontSize: 11,
      },
      emphasis: {
        label: { fontSize: 14, fontWeight: 'bold', color: '#e2e8f0' },
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(34, 211, 238, 0.3)' },
      },
      itemStyle: { borderColor: '#0d1117', borderWidth: 3 },
    }],
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
  } : null;

  /* ── 指标对比柱状图 ────────────────────────────── */
  const barOption = result?.metrics ? {
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: ['互动率', '点赞率', '评论率', '分享率'],
      axisLabel: { color: '#64748b', fontSize: 12 },
    },
    yAxis: { type: 'value', axisLabel: { color: '#64748b', formatter: '{value}%' }, splitLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.2)', type: 'dashed' } } },
    series: [{
      type: 'bar',
      data: [
        { value: parseFloat(result.metrics.engagement_rate) || 0, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#22d3ee' }, { offset: 1, color: '#0891b2' }] }, borderRadius: [8, 8, 0, 0] } },
        { value: parseFloat(result.metrics.like_rate) || 0, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#3b82f6' }, { offset: 1, color: '#1d4ed8' }] }, borderRadius: [8, 8, 0, 0] } },
        { value: parseFloat(result.metrics.comment_rate) || 0, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#a78bfa' }, { offset: 1, color: '#7c3aed' }] }, borderRadius: [8, 8, 0, 0] } },
        { value: parseFloat(result.metrics.share_rate) || 0, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#fbbf24' }, { offset: 1, color: '#d97706' }] }, borderRadius: [8, 8, 0, 0] } },
      ],
      barWidth: 40,
      label: { show: true, position: 'top', color: '#e2e8f0', fontSize: 13, fontWeight: 'bold', formatter: '{c}%' },
    }],
    tooltip: { trigger: 'axis' },
  } : null;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-txt-bright flex items-center gap-3">
          <span className="w-1 h-6 rounded-full bg-gradient-to-b from-amber-400 to-red-500" />
          数据分析
        </h2>
        <p className="text-sm text-txt-secondary mt-1">输入内容数据，获取 AI 深度诊断与优化建议</p>
      </div>

      <div className="card-glow p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">内容标题</label>
            <input type="text" className="input" placeholder="输入已发布内容的标题..." value={contentTitle} onChange={(e) => setContentTitle(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              <option value="xiaohongshu">小红书</option><option value="douyin">抖音</option>
              <option value="bilibili">B站</option><option value="weibo">微博</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { key: 'views', val: views, set: setViews, label: '播放量', icon: '👁️' },
            { key: 'likes', val: likes, set: setLikes, label: '点赞数', icon: '❤️' },
            { key: 'comments', val: comments, set: setComments, label: '评论数', icon: '💬' },
            { key: 'shares', val: shares, set: setShares, label: '分享数', icon: '🔄' },
          ].map((m) => (
            <div key={m.key}>
              <label className="block text-sm font-medium text-txt-secondary mb-1.5">{m.icon} {m.label}</label>
              <input type="number" className="input" placeholder="0" value={m.val} onChange={(e) => m.set(e.target.value)} />
            </div>
          ))}
        </div>
        <button className="btn-primary w-full" onClick={handleAnalyze} disabled={loading || !contentTitle.trim()}>
          {loading ? <><span className="animate-spin">⏳</span> 分析中...</> : '📈 开始分析'}
        </button>
      </div>

      {loading && (
        <div className="card p-8 text-center">
          <div className="inline-block w-8 h-8 border-4 border-brand-500/30 border-t-brand-400 rounded-full animate-spin mb-3" />
          <p className="text-txt-secondary">数据分析引擎运行中...</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-4 animate-slide-up">
          {/* KPI 卡片 */}
          {result.metrics && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatsCard label="互动率" value={parseFloat(result.metrics.engagement_rate) || 0} unit="%" icon="💬" color="cyan" />
              <StatsCard label="点赞率" value={parseFloat(result.metrics.like_rate) || 0} unit="%" icon="❤️" color="blue" />
              <StatsCard label="评论率" value={parseFloat(result.metrics.comment_rate) || 0} unit="%" icon="📝" color="purple" />
              <StatsCard label="分享率" value={parseFloat(result.metrics.share_rate) || 0} unit="%" icon="🔄" color="amber" />
            </div>
          )}

          {/* 图表 */}
          {ringOption && barOption && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-txt-primary mb-2 flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-brand-400" />
                  指标占比
                </h3>
                <DashboardChart option={ringOption} height={300} />
              </div>
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-txt-primary mb-2 flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-blue-400" />
                  指标对比
                </h3>
                <DashboardChart option={barOption} height={300} />
              </div>
            </div>
          )}

          {/* 诊断 */}
          <div className="card p-5">
            <h3 className="text-base font-semibold text-txt-primary mb-2">🔍 AI 诊断</h3>
            <p className="text-sm text-txt-secondary leading-relaxed">{result.diagnosis}</p>
          </div>

          {/* 建议 */}
          {result.suggestions?.length > 0 && (
            <div className="card p-5">
              <h3 className="text-base font-semibold text-txt-primary mb-3">💡 优化建议</h3>
              <div className="space-y-3">
                {result.suggestions.map((s, i) => (
                  <div key={i} className="flex gap-3 p-3 rounded-xl bg-panel-100/50 border border-panel-border/50">
                    <span className="text-lg flex-shrink-0">{i === 0 ? '🎯' : i === 1 ? '📌' : '💡'}</span>
                    <div>
                      <h4 className="text-sm font-medium text-txt-bright">{s.area}</h4>
                      <p className="text-sm text-txt-secondary mt-0.5">{s.suggestion}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
