import { useState, useEffect, useCallback } from 'react';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书', color: '#FF2442', icon: '📕' },
  { id: 'douyin', name: '抖音', color: '#161823', icon: '🎵' },
  { id: 'weixin_video', name: '视频号', color: '#07C160', icon: '📹' },
];

const STATUS_MAP = {
  pending: { label: '待发布', color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
  publishing: { label: '发布中', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
  success: { label: '已发布', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  failed: { label: '失败', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
};

export default function PublishExecPanel() {
  const [platform, setPlatform] = useState('xiaohongshu');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [publishing, setPublishing] = useState(false);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/publish/history');
      const data = await res.json();
      setHistory(data.records || []);
    } catch (e) {
      console.error('加载发布历史失败:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const handlePublish = async () => {
    if (!title.trim() || !content.trim()) {
      setMessage({ type: 'error', text: '标题和内容不能为空' });
      return;
    }
    setPublishing(true);
    setMessage(null);
    try {
      const res = await fetch('/api/publish/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform,
          title,
          content,
          tags: tags.split(/[,，\s]+/).filter(Boolean),
        }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        setMessage({ type: 'success', text: `发布成功！链接: ${data.platform_post_url || '—'}` });
        setTitle('');
        setContent('');
        setTags('');
        loadHistory();
      } else {
        setMessage({ type: 'error', text: data.error_message || '发布失败' });
      }
    } catch (e) {
      setMessage({ type: 'error', text: `发布异常: ${e.message}` });
    } finally {
      setPublishing(false);
    }
  };

  const plat = PLATFORMS.find(p => p.id === platform);

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div>
        <h2 className="text-xl font-bold text-txt-bright flex items-center gap-2">
          <span>📡</span> 多平台发布
        </h2>
        <p className="text-txt-muted text-sm mt-1">将创作内容一键发布到各平台</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 发布表单 */}
        <div className="bg-panel-50/60 backdrop-blur-sm rounded-2xl border border-panel-border p-6">
          <h3 className="text-txt-bright font-semibold mb-4">发布内容</h3>

          {/* 平台选择 */}
          <div className="mb-4">
            <label className="block text-txt-secondary text-sm mb-2">选择平台</label>
            <div className="flex gap-3">
              {PLATFORMS.map(p => (
                <button
                  key={p.id}
                  onClick={() => setPlatform(p.id)}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border transition-all ${
                    platform === p.id
                      ? 'bg-brand-500/15 text-brand-300 border-brand-500/30'
                      : 'bg-panel-100/60 text-txt-secondary border-panel-border hover:border-brand-500/20'
                  }`}
                >
                  <span>{p.icon}</span>
                  <span>{p.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 标题 */}
          <div className="mb-4">
            <label className="block text-txt-secondary text-sm mb-2">标题</label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="输入发布标题..."
              className="w-full bg-panel-100/80 border border-panel-border rounded-xl px-4 py-3 text-txt-bright text-sm placeholder:text-txt-muted/50 focus:border-brand-500/50 focus:outline-none transition-colors"
            />
          </div>

          {/* 内容 */}
          <div className="mb-4">
            <label className="block text-txt-secondary text-sm mb-2">正文内容</label>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="输入发布内容..."
              rows={6}
              className="w-full bg-panel-100/80 border border-panel-border rounded-xl px-4 py-3 text-txt-bright text-sm placeholder:text-txt-muted/50 focus:border-brand-500/50 focus:outline-none transition-colors resize-none"
            />
          </div>

          {/* 标签 */}
          <div className="mb-4">
            <label className="block text-txt-secondary text-sm mb-2">标签（逗号分隔）</label>
            <input
              type="text"
              value={tags}
              onChange={e => setTags(e.target.value)}
              placeholder="AI, 自媒体, 效率工具"
              className="w-full bg-panel-100/80 border border-panel-border rounded-xl px-4 py-3 text-txt-bright text-sm placeholder:text-txt-muted/50 focus:border-brand-500/50 focus:outline-none transition-colors"
            />
          </div>

          {/* 提示 */}
          {message && (
            <div className={`mb-4 px-4 py-3 rounded-xl text-sm border ${
              message.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                : 'bg-red-500/10 border-red-500/20 text-red-400'
            }`}>
              {message.text}
            </div>
          )}

          {/* 发布按钮 */}
          <button
            onClick={handlePublish}
            disabled={publishing}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-brand-500/20 hover:bg-brand-500/30 text-brand-300 font-medium text-sm border border-brand-500/30 hover:border-brand-400/50 transition-all disabled:opacity-50"
          >
            {publishing ? (
              <>
                <div className="w-4 h-4 border-2 border-brand-400/30 border-t-brand-400 rounded-full animate-spin" />
                发布中...
              </>
            ) : (
              <>发布到 {plat?.icon} {plat?.name}</>
            )}
          </button>
        </div>

        {/* 发布历史 */}
        <div className="bg-panel-50/60 backdrop-blur-sm rounded-2xl border border-panel-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-txt-bright font-semibold">发布历史</h3>
            <button onClick={loadHistory} className="text-xs text-txt-muted hover:text-brand-400 transition-colors">
              刷新
            </button>
          </div>
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-400 rounded-full animate-spin" />
            </div>
          ) : history.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-txt-muted">
              <span className="text-3xl mb-2">📭</span>
              <span className="text-sm">暂无发布记录</span>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {history.map((record, idx) => {
                const st = STATUS_MAP[record.status] || STATUS_MAP.pending;
                const p = PLATFORMS.find(p => p.id === record.platform);
                return (
                  <div key={idx} className="p-4 rounded-xl bg-panel-100/40 border border-panel-border hover:border-brand-500/20 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span>{p?.icon || '🌐'}</span>
                        <span className="text-txt-bright text-sm font-medium truncate">{record.title}</span>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${st.bg} ${st.color} flex-shrink-0`}>
                        {st.label}
                      </span>
                    </div>
                    <p className="text-txt-muted text-xs truncate mb-2">{record.content}</p>
                    {record.platform_post_url && (
                      <a href={record.platform_post_url} target="_blank" rel="noopener noreferrer"
                        className="text-xs text-brand-400 hover:text-brand-300 transition-colors">
                        查看链接 →
                      </a>
                    )}
                    {record.error_message && (
                      <p className="text-xs text-red-400 mt-1">{record.error_message}</p>
                    )}
                    <p className="text-txt-muted/60 text-xs mt-2">
                      {record.published_at || record.created_at || ''}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
