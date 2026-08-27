import { useState } from 'react';
import { optimizeTitle } from '../api/client';
import { withLLMProvider } from '../utils/llmProvider';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

export default function TitleOptimizer() {
  const [title, setTitle] = useState('');
  const [platform, setPlatform] = useState('xiaohongshu');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleOptimize = async () => {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const data = await optimizeTitle(withLLMProvider({ title, platform }));
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
        <h2 className="text-2xl font-bold text-gray-900">标题优化</h2>
        <p className="text-sm text-gray-500 mt-1">分析并优化现有标题，提升点击率和传播力</p>
      </div>

      <div className="card p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">目标平台</label>
          <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
            {PLATFORMS.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">原始标题</label>
          <input
            type="text"
            className="input"
            placeholder="粘贴需要优化的标题..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleOptimize()}
          />
        </div>
        <button className="btn-primary w-full" onClick={handleOptimize} disabled={loading || !title.trim()}>
          {loading ? (
            <><span className="animate-spin">⏳</span> 正在分析...</>
          ) : '🔧 分析并优化'}
        </button>
      </div>

      {result && (
        <div className="space-y-4 animate-slide-up">
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-500 mb-2">原始标题</h3>
            <p className="text-lg text-gray-800">{result.original_title}</p>
          </div>

          <h3 className="text-lg font-semibold text-gray-800">优化方案</h3>
          {result.optimized_options?.map((opt, i) => (
            <div key={i} className="card p-5 hover:shadow-card-hover transition-shadow">
              <div className="flex items-start justify-between gap-3 mb-3">
                <h4 className="text-base font-semibold text-gray-900 flex-1">{opt.title}</h4>
                <span className="tag-green">热度 {opt.predicted_heat}</span>
              </div>
              <p className="text-sm text-gray-500 mb-3">{opt.reason}</p>
              {opt.changes?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {opt.changes.map((c, j) => (
                    <span key={j} className="tag-purple">{c}</span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {result.tips?.length > 0 && (
            <div className="card-flat p-5 bg-amber-50/50 border-amber-100">
              <h4 className="text-sm font-semibold text-amber-700 mb-2">💡 优化建议</h4>
              <ul className="space-y-1">
                {result.tips.map((tip, i) => (
                  <li key={i} className="text-sm text-amber-800">• {tip}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
