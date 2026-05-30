import { useState } from 'react';
import { generateCover } from '../api/client';
import { withLLMProvider } from '../utils/llmProvider';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

export default function CoverPanel() {
  const [title, setTitle] = useState('');
  const [platform, setPlatform] = useState('xiaohongshu');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const data = await generateCover(withLLMProvider({ title, platform }));
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
        <h2 className="text-2xl font-bold text-gray-900">封面设计策略</h2>
        <p className="text-sm text-gray-500 mt-1">生成高点击率的封面文案、排版和配色方案</p>
      </div>

      <div className="card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">内容标题</label>
            <input
              type="text"
              className="input"
              placeholder="输入标题..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">目标平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        </div>
        <button className="btn-primary w-full" onClick={handleGenerate} disabled={loading || !title.trim()}>
          {loading ? <><span className="animate-spin">⏳</span> 生成中...</> : '🎨 生成封面方案'}
        </button>
      </div>

      {result && (
        <div className="space-y-4 animate-slide-up">
          {/* 封面文案 */}
          {result.cover_texts?.map((ct, i) => (
            <div key={i} className="card p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="tag-blue">方案 {i + 1}</span>
                <span className="text-sm text-gray-400">{ct.style}</span>
              </div>

              {/* 模拟封面预览 */}
              <div
                className="rounded-2xl p-8 mb-4 text-center min-h-[200px] flex flex-col items-center justify-center"
                style={{
                  background: ct.background_suggestion?.includes('gradient')
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                    : ct.background_suggestion?.includes('暖') ? 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
                    : 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                }}
              >
                <h3 className="text-2xl md:text-3xl font-bold text-white drop-shadow-lg leading-tight mb-3">
                  {ct.main_text}
                </h3>
                {ct.sub_text && (
                  <p className="text-white/80 text-base">{ct.sub_text}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">主文案</span>
                  <p className="font-medium text-gray-800">{ct.main_text}</p>
                </div>
                <div>
                  <span className="text-gray-400">副文案</span>
                  <p className="font-medium text-gray-800">{ct.sub_text || '无'}</p>
                </div>
                <div>
                  <span className="text-gray-400">字体风格</span>
                  <p className="font-medium text-gray-800">{ct.font_style}</p>
                </div>
                <div>
                  <span className="text-gray-400">背景建议</span>
                  <p className="font-medium text-gray-800">{ct.background_suggestion}</p>
                </div>
              </div>
            </div>
          ))}

          {result.design_tips?.length > 0 && (
            <div className="card-flat p-5 bg-indigo-50/50 border-indigo-100">
              <h4 className="text-sm font-semibold text-indigo-700 mb-2">🎨 设计建议</h4>
              <ul className="space-y-1">
                {result.design_tips.map((t, i) => <li key={i} className="text-sm text-indigo-800">• {t}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
