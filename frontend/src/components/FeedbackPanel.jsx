import { useState } from 'react';
import { analyzeFeedback } from '../api/client';

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
      const data = await analyzeFeedback({ content_title: contentTitle, comments: commentList, platform });
      setResult(data);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const sentimentColor = (s) => {
    if (s === '正面') return 'bg-emerald-50 text-emerald-700';
    if (s === '负面') return 'bg-red-50 text-red-700';
    return 'bg-gray-50 text-gray-600';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">评论智能分析</h2>
        <p className="text-sm text-gray-500 mt-1">粘贴用户评论，AI 深度解析情感倾向与优化方向</p>
      </div>

      <div className="card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">内容标题</label>
            <input
              type="text"
              className="input"
              placeholder="对应内容的标题"
              value={contentTitle}
              onChange={(e) => setContentTitle(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">用户评论（每行一条）</label>
          <textarea
            className="textarea h-40"
            placeholder={"好有用！收藏了\n请问这个产品在哪买？\n感觉不太适合油皮\n太棒了 已经跟着做了"}
            value={comments}
            onChange={(e) => setComments(e.target.value)}
          />
        </div>
        <button className="btn-primary w-full" onClick={handleAnalyze} disabled={loading || !contentTitle.trim() || !comments.trim()}>
          {loading ? <><span className="animate-spin">⏳</span> 分析中...</> : '💬 开始分析'}
        </button>
      </div>

      {result && (
        <div className="space-y-6 animate-slide-up">
          {/* 情感分布 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">📊 情感分布</h3>
            <div className="grid grid-cols-3 gap-3">
              {result.sentiment_breakdown?.map((s, i) => (
                <div key={i} className="card p-5 text-center">
                  <p className={`text-2xl font-bold ${s.sentiment === '正面' ? 'text-emerald-600' : s.sentiment === '负面' ? 'text-red-600' : 'text-gray-600'}`}>
                    {s.percentage}%
                  </p>
                  <p className="text-sm text-gray-500 mt-1">{s.sentiment}</p>
                  <p className="text-xs text-gray-400 mt-1">{s.count} 条</p>
                </div>
              ))}
            </div>
          </div>

          {/* 关键主题 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">🏷️ 关键主题</h3>
            <div className="grid gap-2">
              {result.key_themes?.map((t, i) => (
                <div key={i} className="card-flat p-4 flex items-center gap-4">
                  <span className="text-lg">📌</span>
                  <div className="flex-1 min-w-0">
                    <span className="font-medium text-gray-900">{t.theme}</span>
                    <span className="ml-2 text-sm text-gray-400">{t.count} 次提及</span>
                  </div>
                  <span className={`tag ${sentimentColor(t.sentiment)}`}>{t.sentiment}</span>
                  <span className="tag-gray text-xs max-w-xs truncate">{t.example}</span>
                </div>
              ))}
            </div>
          </div>

          {/* AI 建议 */}
          {result.suggestions?.length > 0 && (
            <div className="card-flat p-5 bg-emerald-50/50 border-emerald-100">
              <h4 className="text-sm font-semibold text-emerald-700 mb-2">🎯 AI 优化建议</h4>
              <ul className="space-y-1.5">
                {result.suggestions.map((s, i) => (
                  <li key={i} className="text-sm text-emerald-800">• {s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
