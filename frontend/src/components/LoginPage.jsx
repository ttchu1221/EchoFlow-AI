import { useState } from 'react';

const API = '/api/auth';

export default function LoginPage({ onLogin, onForgotPassword }) {
  const [mode, setMode] = useState('login'); // login | register
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const url = mode === 'login' ? `${API}/login` : `${API}/register`;
      const body = mode === 'login'
        ? { username, password }
        : { username, password, display_name: displayName || username };

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail?.error || data.detail || '操作失败');
      }

      const { access_token, refresh_token, user } = data.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      onLogin(user, access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-panel grid-bg">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-lg shadow-brand-500/25 mb-4">
            <span className="text-3xl">🚀</span>
          </div>
          <h1 className="text-2xl font-bold text-txt-primary">EchoFlow AI</h1>
          <p className="text-txt-muted text-sm mt-1">AI Native 内容增长运营系统</p>
        </div>

        {/* 表单卡片 */}
        <div className="bg-panel-50/80 backdrop-blur-sm border border-panel-border rounded-2xl p-8 shadow-xl">
          {/* 切换标签 */}
          <div className="flex mb-6 bg-panel-100 rounded-xl p-1">
            <button
              onClick={() => { setMode('login'); setError(''); }}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                mode === 'login'
                  ? 'bg-brand-500 text-white shadow'
                  : 'text-txt-muted hover:text-txt-primary'
              }`}
            >
              登录
            </button>
            <button
              onClick={() => { setMode('register'); setError(''); }}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                mode === 'register'
                  ? 'bg-brand-500 text-white shadow'
                  : 'text-txt-muted hover:text-txt-primary'
              }`}
            >
              注册
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-txt-secondary mb-1.5">用户名</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-txt-primary placeholder-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500"
                placeholder="3-32 位字母、数字、下划线"
                required
                minLength={3}
              />
            </div>

            {mode === 'register' && (
              <div>
                <label className="block text-sm text-txt-secondary mb-1.5">显示名称</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-txt-primary placeholder-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500"
                  placeholder="可选，默认为用户名"
                />
              </div>
            )}

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-sm text-txt-secondary">密码</label>
                {mode === 'login' && onForgotPassword && (
                  <button
                    type="button"
                    onClick={onForgotPassword}
                    className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                  >
                    忘记密码？
                  </button>
                )}
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-txt-primary placeholder-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500"
                placeholder="至少 6 位"
                required
                minLength={6}
              />
            </div>

            {error && (
              <div className="px-4 py-2.5 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 text-white font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-brand-500/25"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  处理中...
                </span>
              ) : mode === 'login' ? '登录' : '注册'}
            </button>
          </form>

          {mode === 'register' && (
            <p className="text-xs text-txt-muted text-center mt-4">
              第一个注册的用户将自动成为管理员
            </p>
          )}
        </div>

        <p className="text-center text-xs text-txt-muted mt-6">
          EchoFlow AI v1.4 — AI Native 内容增长运营系统
        </p>
      </div>
    </div>
  );
}
