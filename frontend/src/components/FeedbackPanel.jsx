import { useState } from 'react';
import { analyzeFeedback } from '../api/client';
import { withLLMProvider } from '../utils/llmProvider';
import DashboardChart, { NEON_COLORS } from './DashboardChart';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

export default function FeedbackPanel() {
  const [contentTitle, setContentTitle] = useState('');
  const [comments, setComments] = useState('');
  const [platform, setPlatform] = useState('xiaohongshu');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!contentTitle.trim() || !comments.trim()) return;
    setLoading(true);
    try {
      const commentList = comments.split('\n').filter((l) => l.trim());
      const data = await analyzeFeedback(withLLMProvider({ content_title: contentTitle, comments: commentList, platform }));
      setResult(data);
    } catch (e) { alert(e.message); } finally { setLoading(false); }
  };

  /* ── 情感饼图 ──────────────────────────────────── */
  const sentimentPieOption = result?.sentiment_breakdown ? {
    series: [{
      type: 'pie', radius: ['48%', '72%'], center: ['50%', '50%'],
      data: result.sentiment_breakdown.map(s => ({
        value: s.count || parseFloat(s.percentage) || 0,
        name: s.sentiment,
        itemStyle: {
          color: s.sentiment === '正面' ? '#34d399' : s.sentiment === '负面' ? '#f87171' : '#64748b',
        },
      })),
      label: {
        show: true, color: '#94a3b8', fontSize: 12,
        formatter: '{b}\n{c}条 ({d}%)',
      },
      emphasis: {
        label: { fontSize: 14, fontWeight: 'bold', color: '#e2e8f0' },
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(34, 211, 238, 0.3)' },
      },
      itemStyle: { borderColor: '#0d1117', borderWidth: 3 },
    }],
    tooltip: { trigger: 'item' },
  } : null;

  /* ── 主题提及柱状图 ────────────────────────────── */
  const themeBarOption = result?.key_themes ? {
    grid: { left: 120, right: 40, top: 10, bottom: 30 },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category',
      data: result.key_themes.map(t => t.theme).reverse(),
      axisLabel: { color: '#94a3b8', fontSize: 11, width: 100, overflow: 'truncate' },
      axisLine: { show: false }, axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: result.key_themes.map((t, i) => ({
        value: t.count || 0,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: (t.sentiment === '正面' ? { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: 'rgba(52,211,153,0.1)' }, { offset: 1, color: '#34d399' }] }
            : t.sentiment === '负面' ? { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: 'rgba(248,113,113,0.1)' }, { offset: 1, color: '#f87171' }] }
            : { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: 'rgba(100,116,139,0.1)' }, { offset: 1, color: '#64748b' }] }),
        },
      })).reverse(),
      barWidth: 16,
      label: { show: true, position: 'right', color: '#e2e8f0', fontSize: 12, formatter: '{c} 次' },
    }],
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  } : null;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-txt-bright flex items-center gap-3">
          <span className="w-1 h-6 rounded-full bg-gradient-to-b from-pink-400 to-purple-600" />
          评论智能分析
        </h2>
        <p className="text-sm text-txt-secondary mt-1">粘贴用户评论，AI 深度解析情感倾向与优化方向</p>
      </div>

      <div className="card-glow p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">内容标题</label>
            <input type="text" className="input" placeholder="对应内容的标题" value={contentTitle} onChange={(e) => setContentTitle(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-txt-secondary mb-1.5">用户评论（每行一条）</label>
          <textarea className="textarea h-40" placeholder={"好有用！收藏了\n请问这个产品在哪买？\n感觉不太适合油皮\n太棒了 已经跟着做了"} value={comments} onChange={(e) => setComments(e.target.value)} />
        </div>
        <button className="btn-primary w-full" onClick={handleAnalyze} disabled={loading || !contentTitle.trim() || !comments.trim()}>
          {loading ? <><span className="animate-spin">⏳</span> 分析中...</> : '💬 开始分析'}
        </button>
      </div>

      {loading && (
        <div className="card p-8 text-center">
          <div className="inline-block w-8 h-8 border-4 border-pink-500/30 border-t-pink-400 rounded-full animate-spin mb-3" />
          <p className="text-txt-secondary">评论分析引擎运行中...</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-6 animate-slide-up">
          {/* 图表区 */}
          {sentimentPieOption && themeBarOption && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-txt-primary mb-2 flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-emerald-400" />
                  情感分布
                </h3>
                <DashboardChart option={sentimentPieOption} height={300} />
              </div>
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-txt-primary mb-2 flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-brand-400" />
                  主题提及频率
                </h3>
                <DashboardChart option={themeBarOption} height={Math.max(250, (result.key_themes?.length || 3) * 45)} />
              </div>
            </div>
          )}

          {/* 关键主题详情 */}
          <div>
            <h3 className="text-lg font-semibold text-txt-primary mb-3">🏷️ 关键主题</h3>
            <div className="grid gap-2">
              {result.key_themes?.map((t, i) => (
                <div key={i} className="card-flat p-4 flex items-center gap-4">
                  <span className="text-lg">📌</span>
                  <div className="flex-1 min-w-0">
                    <span className="font-medium text-txt-bright">{t.theme}</span>
                    <span className="ml-2 text-sm text-txt-muted">{t.count} 次提及</span>
                  </div>
                  <span className={t.sentiment === '正面' ? 'tag-green' : t.sentiment === '负面' ? 'tag-red' : 'tag-gray'}>{t.sentiment}</span>
                  <span className="tag-gray text-xs max-w-xs truncate">{t.example}</span>
                </div>
              ))}
            </div>
          </div>

          {/* AI 建议 */}
          {result.suggestions?.length > 0 && (
            <div className="card p-5 bg-emerald-500/5 border-emerald-500/20">
              <h4 className="text-sm font-semibold text-emerald-400 mb-2">🎯 AI 优化建议</h4>
              <ul className="space-y-1.5">
                {result.suggestions.map((s, i) => <li key={i} className="text-sm text-emerald-300/80">• {s}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
