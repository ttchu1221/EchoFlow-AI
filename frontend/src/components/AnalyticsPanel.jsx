import { useState } from 'react';
import { analyzePerformance } from '../api/client';

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
      const data = await analyzePerformance({
        content_title: contentTitle,
        metrics: {
          views: parseInt(views) || 0,
          likes: parseInt(likes) || 0,
          comments: parseInt(comments) || 0,
          shares: parseInt(shares) || 0,
        },
        platform,
      });
      setResult(data);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">数据分析</h2>
        <p className="text-sm text-gray-500 mt-1">输入内容数据，获取 AI 深度诊断与优化建议</p>
      </div>

      <div className="card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">内容标题</label>
            <input
              type="text"
              className="input"
              placeholder="输入已发布内容的标题..."
              value={contentTitle}
              onChange={(e) => setContentTitle(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              <option value="xiaohongshu">小红书</option>
              <option value="douyin">抖音</option>
              <option value="bilibili">B站</option>
              <option value="weibo">微博</option>
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
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                {m.icon} {m.label}
              </label>
              <input
                type="number"
                className="input"
                placeholder="0"
                value={m.val}
                onChange={(e) => m.set(e.target.value)}
              />
            </div>
          ))}
        </div>

        <button className="btn-primary w-full" onClick={handleAnalyze} disabled={loading || !contentTitle.trim()}>
          {loading ? <><span className="animate-spin">⏳</span> 分析中...</> : '📈 开始分析'}
        </button>
      </div>

      {result && (
        <div className="space-y-4 animate-slide-up">
          {/* 核心指标 */}
          {result.metrics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="card p-5 text-center">
                <p className="text-2xl font-bold text-brand-600">{result.metrics.engagement_rate}%</p>
                <p className="text-xs text-gray-500 mt-1">互动率</p>
              </div>
              <div className="card p-5 text-center">
                <p className="text-2xl font-bold text-emerald-600">{result.metrics.like_rate}%</p>
                <p className="text-xs text-gray-500 mt-1">点赞率</p>
              </div>
              <div className="card p-5 text-center">
                <p className="text-2xl font-bold text-purple-600">{result.metrics.comment_rate}%</p>
                <p className="text-xs text-gray-500 mt-1">评论率</p>
              </div>
              <div className="card p-5 text-center">
                <p className="text-2xl font-bold text-amber-600">{result.metrics.share_rate}%</p>
                <p className="text-xs text-gray-500 mt-1">分享率</p>
              </div>
            </div>
          )}

          {/* 诊断 */}
          <div className="card p-5">
            <h3 className="text-base font-semibold text-gray-800 mb-2">🔍 AI 诊断</h3>
            <p className="text-sm text-gray-600 leading-relaxed">{result.diagnosis}</p>
          </div>

          {/* 建议 */}
          {result.suggestions?.length > 0 && (
            <div className="card p-5">
              <h3 className="text-base font-semibold text-gray-800 mb-3">💡 优化建议</h3>
              <div className="space-y-3">
                {result.suggestions.map((s, i) => (
                  <div key={i} className="flex gap-3 p-3 rounded-xl bg-gray-50">
                    <span className="text-lg flex-shrink-0">{i === 0 ? '🎯' : i === 1 ? '📌' : '💡'}</span>
                    <div>
                      <h4 className="text-sm font-medium text-gray-800">{s.area}</h4>
                      <p className="text-sm text-gray-500 mt-0.5">{s.suggestion}</p>
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
