import { useState } from 'react';
import { analyzeTrends } from '../api/client';

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
      const data = await analyzeTrends({ topic, platform, time_range: timeRange });
      setResult(data);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const directionColor = (d) => {
    if (d === '上升') return 'text-emerald-600 bg-emerald-50';
    if (d === '下降') return 'text-red-600 bg-red-50';
    return 'text-gray-600 bg-gray-50';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">趋势分析</h2>
        <p className="text-sm text-gray-500 mt-1">结合实时数据与 AI 分析，发现内容趋势与爆款模式</p>
      </div>

      <div className="card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">目标平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">时间范围</label>
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
          <label className="block text-sm font-medium text-gray-700 mb-1.5">分析领域</label>
          <input
            type="text"
            className="input"
            placeholder="例如：护肤、健身、编程教学..."
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          />
        </div>
      </div>

      {result && (
        <div className="space-y-6 animate-slide-up">
          {/* 热门话题 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">🔥 热门话题</h3>
            <div className="grid gap-3">
              {result.trending_topics?.map((t, i) => (
                <div key={i} className="card p-5">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h4 className="font-semibold text-gray-900 flex-1">{t.topic}</h4>
                    <div className="flex gap-2 flex-shrink-0">
                      <span className="tag-blue">热度 {t.heat_score}</span>
                      <span className={`tag ${directionColor(t.trend_direction)}`}>
                        {t.trend_direction === '上升' ? '📈' : t.trend_direction === '下降' ? '📉' : '➡️'} {t.trend_direction}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-500 mb-3">{t.reason}</p>
                  {t.related_keywords?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {t.related_keywords.map((k, j) => (
                        <span key={j} className="tag-gray">#{k}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 爆款模式 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">💡 爆款内容模式</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {result.viral_patterns?.map((p, i) => (
                <div key={i} className="card p-5">
                  <h4 className="font-semibold text-gray-900 mb-2">{p.pattern_name}</h4>
                  <p className="text-sm text-gray-500 mb-3">{p.description}</p>
                  <div className="space-y-1 mb-3">
                    {p.examples?.map((e, j) => (
                      <p key={j} className="text-xs text-gray-400">• {e}</p>
                    ))}
                  </div>
                  <span className="tag-purple">{p.applicability}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 受众洞察 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">👥 受众洞察</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.audience_insights?.map((a, i) => (
                <div key={i} className="card p-5">
                  <h4 className="font-semibold text-gray-900 mb-3">{a.segment}</h4>
                  <div className="space-y-2">
                    <div>
                      <span className="text-xs font-medium text-gray-400">兴趣</span>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {a.interests?.map((t, j) => <span key={j} className="tag-blue">{t}</span>)}
                      </div>
                    </div>
                    <div>
                      <span className="text-xs font-medium text-gray-400">痛点</span>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {a.pain_points?.map((t, j) => <span key={j} className="tag-red">{t}</span>)}
                      </div>
                    </div>
                    <p className="text-sm text-gray-500 mt-2">{a.content_preference}</p>
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
