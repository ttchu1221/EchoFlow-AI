import { useState, useEffect, useCallback } from 'react';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书', color: '#FF2442', icon: '📕', desc: '图文笔记发布与数据采集' },
  { id: 'douyin', name: '抖音', color: '#161823', icon: '🎵', desc: '视频数据采集（发布需创作者中心）' },
  { id: 'weixin_video', name: '视频号', color: '#07C160', icon: '📹', desc: '视频数据采集（发布需视频号助手）' },
];

export default function AccountsPanel() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [binding, setBinding] = useState(null);
  const [showBindModal, setShowBindModal] = useState(false);
  const [bindPlatform, setBindPlatform] = useState('xiaohongshu');
  const [cookies, setCookies] = useState('');
  const [nickname, setNickname] = useState('');
  const [message, setMessage] = useState(null);

  const loadAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/accounts');
      const data = await res.json();
      setAccounts(data.accounts || []);
    } catch (e) {
      console.error('加载账号失败:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAccounts(); }, [loadAccounts]);

  const handleBind = async () => {
    if (!cookies.trim()) {
      setMessage({ type: 'error', text: '请输入 Cookie' });
      return;
    }
    setBinding(bindPlatform);
    setMessage(null);
    try {
      const res = await fetch('/api/accounts/bind', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform: bindPlatform,
          cookies: cookies.trim(),
          nickname: nickname.trim(),
        }),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: `${PLATFORMS.find(p => p.id === bindPlatform)?.name} 绑定成功！` });
        setShowBindModal(false);
        setCookies('');
        setNickname('');
        loadAccounts();
      } else {
        const data = await res.json();
        setMessage({ type: 'error', text: data.detail || '绑定失败' });
      }
    } catch (e) {
      setMessage({ type: 'error', text: `绑定异常: ${e.message}` });
    } finally {
      setBinding(null);
    }
  };

  const handleUnbind = async (platform) => {
    if (!confirm(`确定解绑 ${PLATFORMS.find(p => p.id === platform)?.name}？`)) return;
    try {
      await fetch(`/api/accounts/${platform}`, { method: 'DELETE' });
      loadAccounts();
    } catch (e) {
      console.error('解绑失败:', e);
    }
  };

  const isBound = (platformId) => accounts.some(a => a.platform === platformId);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-txt-bright flex items-center gap-2">
          <span>🔗</span> 平台账号管理
        </h2>
        <p className="text-txt-muted text-sm mt-1">绑定你的平台账号，实现一键发布和数据采集</p>
      </div>

      {/* 消息提示 */}
      {message && (
        <div className={`px-4 py-3 rounded-xl text-sm border ${
          message.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            : 'bg-red-500/10 border-red-500/20 text-red-400'
        }`}>
          {message.text}
        </div>
      )}

      {/* 平台卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {PLATFORMS.map(p => {
          const bound = isBound(p.id);
          const account = accounts.find(a => a.platform === p.id);
          return (
            <div key={p.id} className="bg-panel-50/60 backdrop-blur-sm rounded-2xl border border-panel-border p-6 hover:border-brand-500/20 transition-all">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                  style={{ background: `${p.color}15`, border: `1px solid ${p.color}30` }}>
                  {p.icon}
                </div>
                <div>
                  <h3 className="text-txt-bright font-semibold">{p.name}</h3>
                  <p className="text-txt-muted text-xs">{p.desc}</p>
                </div>
              </div>

              {bound && account ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="text-emerald-400 text-sm">已绑定</span>
                    {account.nickname && (
                      <span className="text-txt-secondary text-sm ml-1">· {account.nickname}</span>
                    )}
                  </div>
                  <button
                    onClick={() => handleUnbind(p.id)}
                    className="w-full px-4 py-2.5 rounded-xl text-sm text-red-400 bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 transition-colors"
                  >
                    解绑
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-panel-100/60 border border-panel-border">
                    <div className="w-2 h-2 rounded-full bg-txt-muted" />
                    <span className="text-txt-muted text-sm">未绑定</span>
                  </div>
                  <button
                    onClick={() => { setBindPlatform(p.id); setShowBindModal(true); }}
                    className="w-full px-4 py-2.5 rounded-xl text-sm text-brand-300 bg-brand-500/15 border border-brand-500/25 hover:bg-brand-500/25 transition-colors"
                  >
                    绑定账号
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 使用说明 */}
      <div className="bg-panel-50/60 backdrop-blur-sm rounded-2xl border border-panel-border p-6">
        <h3 className="text-txt-bright font-semibold mb-3 flex items-center gap-2">
          <span>💡</span> 如何获取 Cookie？
        </h3>
        <div className="space-y-2 text-txt-secondary text-sm">
          <p>1. 用浏览器登录对应平台（如小红书网页版）</p>
          <p>2. 按 <kbd className="px-1.5 py-0.5 rounded bg-panel-100 text-txt-muted text-xs font-mono">F12</kbd> 打开开发者工具</p>
          <p>3. 切换到 <strong className="text-txt-primary">Network（网络）</strong> 标签</p>
          <p>4. 刷新页面，点击任意请求，在 <strong className="text-txt-primary">Headers</strong> 中找到 <code className="text-brand-400">Cookie</code> 字段</p>
          <p>5. 复制整个 Cookie 值粘贴到下方即可</p>
        </div>
        <div className="mt-3 px-4 py-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-xs">
          ⚠️ Cookie 包含你的登录凭证，请勿分享给他人。系统会加密存储，仅用于 API 调用。
        </div>
      </div>

      {/* 绑定弹窗 */}
      {showBindModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-panel-50 border border-panel-border rounded-2xl p-6 w-full max-w-md mx-4">
            <h3 className="text-txt-bright font-semibold text-lg mb-4">
              绑定 {PLATFORMS.find(p => p.id === bindPlatform)?.icon}{' '}
              {PLATFORMS.find(p => p.id === bindPlatform)?.name}
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-txt-secondary text-sm mb-2">昵称（可选）</label>
                <input
                  type="text"
                  value={nickname}
                  onChange={e => setNickname(e.target.value)}
                  placeholder="你的平台昵称"
                  className="w-full bg-panel-100/80 border border-panel-border rounded-xl px-4 py-3 text-txt-bright text-sm placeholder:text-txt-muted/50 focus:border-brand-500/50 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-txt-secondary text-sm mb-2">Cookie</label>
                <textarea
                  value={cookies}
                  onChange={e => setCookies(e.target.value)}
                  placeholder="粘贴从浏览器复制的 Cookie..."
                  rows={4}
                  className="w-full bg-panel-100/80 border border-panel-border rounded-xl px-4 py-3 text-txt-bright text-xs font-mono placeholder:text-txt-muted/50 focus:border-brand-500/50 focus:outline-none resize-none"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => { setShowBindModal(false); setCookies(''); setNickname(''); }}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm text-txt-secondary bg-panel-100 border border-panel-border hover:bg-panel-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleBind}
                disabled={binding === bindPlatform}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm text-brand-300 bg-brand-500/20 border border-brand-500/30 hover:bg-brand-500/30 transition-colors disabled:opacity-50"
              >
                {binding === bindPlatform ? '绑定中...' : '确认绑定'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
