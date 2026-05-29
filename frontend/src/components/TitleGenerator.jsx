import { useState } from 'react';
import { generateTitles } from '../api/client';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

export default function TitleGenerator() {
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('xiaohongshu');
  const [style, setStyle] = useState('mixed');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const data = await generateTitles({ topic, platform, style, count: 5 });
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
        <h2 className="text-2xl font-bold text-gray-900">爆款标题生成</h2>
        <p className="text-sm text-gray-500 mt-1">输入主题，AI 为你生成 5 个优化标题方案</p>
      </div>

      <div className="card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">目标平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">内容风格</label>
            <select className="select" value={style} onChange={(e) => setStyle(e.target.value)}>
              <option value="mixed">混合型</option>
              <option value="emotional">情感共鸣</option>
              <option value="curiosity">好奇心</option>
              <option value="pain_point">痛点直击</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">内容主题</label>
          <input
            type="text"
            className="input"
            placeholder="例如：30天减脂计划、新手化妆教程、职场沟通技巧..."
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
          />
        </div>

        <button className="btn-primary w-full" onClick={handleGenerate} disabled={loading || !topic.trim()}>
          {loading ? (
            <><span className="animate-spin">⏳</span> 正在生成...</>
          ) : '✨ 生成爆款标题'}
        </button>
      </div>

      {result && (
        <div className="space-y-4 animate-slide-up">
          <h3 className="text-lg font-semibold text-gray-800">生成结果</h3>
          {result.titles?.map((item, i) => (
            <div key={i} className="card p-5 hover:shadow-card-hover transition-shadow">
              <div className="flex items-start justify-between gap-3 mb-3">
                <h4 className="text-base font-semibold text-gray-900 flex-1">{item.title}</h4>
                <div className="flex gap-2 flex-shrink-0">
                  <span className="tag-blue">热度 {item.predicted_heat}</span>
                  <span className={item.is_optimized ? 'tag-green' : 'tag-gray'}>
                    {item.is_optimized ? '✓ 已优化' : '原始'}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-500 leading-relaxed">{item.reason}</p>
            </div>
          ))}
          {result.improvement_summary && (
            <div className="card-flat p-5 bg-brand-50/50 border-brand-100">
              <h4 className="text-sm font-semibold text-brand-700 mb-2">📊 优化总结</h4>
              <p className="text-sm text-brand-800 leading-relaxed">{result.improvement_summary}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
