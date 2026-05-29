import { useState } from 'react';
import { generateScript } from '../api/client';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

export default function ScriptPanel() {
  const [title, setTitle] = useState('');
  const [platform, setPlatform] = useState('douyin');
  const [contentType, setContentType] = useState('short_video');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const data = await generateScript({ title, platform, content_type: contentType, duration: '60s' });
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
        <h2 className="text-2xl font-bold text-gray-900">智能脚本生成</h2>
        <p className="text-sm text-gray-500 mt-1">一键生成完整的内容脚本，包含开头、正文、结尾和字幕建议</p>
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
            <label className="block text-sm font-medium text-gray-700 mb-1.5">内容类型</label>
            <select className="select" value={contentType} onChange={(e) => setContentType(e.target.value)}>
              <option value="short_video">短视频</option>
              <option value="note">图文笔记</option>
              <option value="article">长文</option>
              <option value="live">直播</option>
            </select>
          </div>
          <div className="flex items-end">
            <button className="btn-primary w-full" onClick={handleGenerate} disabled={loading || !title.trim()}>
              {loading ? <><span className="animate-spin">⏳</span> 生成中...</> : '📝 生成脚本'}
            </button>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">内容标题</label>
          <input
            type="text"
            className="input"
            placeholder="输入标题或主题..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
          />
        </div>
      </div>

      {result && (
        <div className="space-y-4 animate-slide-up">
          <h3 className="text-lg font-semibold text-gray-800">📄 生成脚本</h3>

          {/* 完整脚本 */}
          <div className="card p-6">
            <pre className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed font-sans">{result.full_script}</pre>
          </div>

          {/* 结构化数据 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.hook && (
              <div className="card-flat p-5 border-l-4 border-brand-400">
                <h4 className="text-sm font-semibold text-brand-700 mb-1">🎣 开场 Hook</h4>
                <p className="text-sm text-gray-700">{result.hook}</p>
              </div>
            )}
            {result.ending && (
              <div className="card-flat p-5 border-l-4 border-emerald-400">
                <h4 className="text-sm font-semibold text-emerald-700 mb-1">🎬 结尾 CTA</h4>
                <p className="text-sm text-gray-700">{result.ending}</p>
              </div>
            )}
          </div>

          {result.subtitles?.length > 0 && (
            <div className="card p-5">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">💬 字幕建议</h4>
              <div className="flex flex-wrap gap-2">
                {result.subtitles.map((s, i) => <span key={i} className="tag-blue">{s}</span>)}
              </div>
            </div>
          )}

          {result.tips?.length > 0 && (
            <div className="card-flat p-5 bg-purple-50/50 border-purple-100">
              <h4 className="text-sm font-semibold text-purple-700 mb-2">💡 拍摄建议</h4>
              <ul className="space-y-1">
                {result.tips.map((t, i) => <li key={i} className="text-sm text-purple-800">• {t}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
