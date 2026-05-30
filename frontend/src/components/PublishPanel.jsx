import { useState } from 'react';
import { planPublish } from '../api/client';
import { withLLMProvider } from '../utils/llmProvider';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

export default function PublishPanel() {
  const [title, setTitle] = useState('');
  const [platform, setPlatform] = useState('xiaohongshu');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePlan = async () => {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const data = await planPublish(withLLMProvider({ title, platform }));
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
        <h2 className="text-2xl font-bold text-gray-900">发布策略规划</h2>
        <p className="text-sm text-gray-500 mt-1">智能规划发布时间、话题标签和推广策略</p>
      </div>

      <div className="card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">内容标题</label>
            <input
              type="text"
              className="input"
              placeholder="输入要发布的内容标题..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handlePlan()}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        </div>
        <button className="btn-primary w-full" onClick={handlePlan} disabled={loading || !title.trim()}>
          {loading ? <><span className="animate-spin">⏳</span> 规划中...</> : '📡 生成发布策略'}
        </button>
      </div>

      {result && (
        <div className="space-y-4 animate-slide-up">
          {/* 发布时间 */}
          {result.publish_time && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">⏰ 最佳发布时间</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="text-center p-4 rounded-xl bg-brand-50">
                  <p className="text-2xl font-bold text-brand-600">{result.publish_time.best_time}</p>
                  <p className="text-sm text-gray-500 mt-1">推荐时间</p>
                </div>
                <div className="sm:col-span-2">
                  <p className="text-sm text-gray-600 mb-2">{result.publish_time.reason}</p>
                  <div className="flex flex-wrap gap-2">
                    {result.publish_time.alternative_times?.map((t, i) => (
                      <span key={i} className="tag-gray">{t}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 话题标签 */}
          {result.hashtags?.length > 0 && (
            <div className="card p-5">
              <h3 className="text-base font-semibold text-gray-800 mb-3">#️⃣ 推荐话题标签</h3>
              <div className="flex flex-wrap gap-2">
                {result.hashtags.map((tag, i) => (
                  <span key={i} className="tag-blue">#{tag}</span>
                ))}
              </div>
            </div>
          )}

          {/* 描述模板 */}
          {result.description_template && (
            <div className="card p-5">
              <h3 className="text-base font-semibold text-gray-800 mb-2">📝 描述模板</h3>
              <pre className="text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 rounded-xl p-4">{result.description_template}</pre>
            </div>
          )}

          {/* 推广策略 */}
          {result.promotion_strategy && (
            <div className="card p-5">
              <h3 className="text-base font-semibold text-gray-800 mb-3">📈 推广策略</h3>
              <p className="text-sm text-gray-600 mb-3">{result.promotion_strategy.strategy}</p>
              {result.promotion_strategy.tips?.length > 0 && (
                <ul className="space-y-1">
                  {result.promotion_strategy.tips.map((t, i) => (
                    <li key={i} className="text-sm text-gray-500">• {t}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* 注意事项 */}
          {result.platform_tips?.length > 0 && (
            <div className="card-flat p-5 bg-amber-50/50 border-amber-100">
              <h4 className="text-sm font-semibold text-amber-700 mb-2">⚠️ 注意事项</h4>
              <ul className="space-y-1">
                {result.platform_tips.map((t, i) => <li key={i} className="text-sm text-amber-800">• {t}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
