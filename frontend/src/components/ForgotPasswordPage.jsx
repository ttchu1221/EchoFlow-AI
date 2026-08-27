import { useState } from 'react';

const API = '/api/auth';

export default function ForgotPasswordPage({ onBack }) {
  const [step, setStep] = useState(1); // 1: 输入用户名, 2: 输入令牌+新密码, 3: 成功
  const [username, setUsername] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRequestToken = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch(`${API}/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail?.error || data.detail || '请求失败');
      }

      // 自托管模式：直接显示令牌
      if (data.data?.token) {
        setToken(data.data.token);
      }
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');

    if (newPassword !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API}/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, token, new_password: newPassword }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail?.error || data.detail || '重置失败');
      }

      // 自动登录
      const { access_token, user } = data.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      setStep(3);
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
            <span className="text-3xl">🔑</span>
          </div>
          <h1 className="text-2xl font-bold text-txt-primary">重置密码</h1>
          <p className="text-txt-muted text-sm mt-1">EchoFlow AI</p>
        </div>

        {/* 表单卡片 */}
        <div className="bg-panel-50/80 backdrop-blur-sm border border-panel-border rounded-2xl p-8 shadow-xl">

          {/* Step 1: 输入用户名 */}
          {step === 1 && (
            <form onSubmit={handleRequestToken} className="space-y-4">
              <p className="text-txt-secondary text-sm mb-2">
                输入你的用户名，系统将生成重置令牌。
              </p>
              <div>
                <label className="block text-sm text-txt-secondary mb-1.5">用户名</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-txt-primary placeholder-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500"
                  placeholder="请输入用户名"
                  required
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
                ) : '获取重置令牌'}
              </button>
            </form>
          )}

          {/* Step 2: 输入令牌 + 新密码 */}
          {step === 2 && (
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div className="px-4 py-3 bg-brand-500/10 border border-brand-500/30 rounded-xl text-brand-300 text-sm">
                <p className="font-medium mb-1">重置令牌已生成</p>
                <p className="text-txt-muted text-xs">令牌有效期 15 分钟，请尽快完成重置。</p>
              </div>

              <div>
                <label className="block text-sm text-txt-secondary mb-1.5">重置令牌</label>
                <input
                  type="text"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-txt-primary placeholder-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 font-mono tracking-widest text-center text-lg"
                  placeholder="输入 6 位令牌"
                  required
                  maxLength={6}
                />
              </div>

              <div>
                <label className="block text-sm text-txt-secondary mb-1.5">新密码</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-txt-primary placeholder-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500"
                  placeholder="至少 6 位"
                  required
                  minLength={6}
                />
              </div>

              <div>
                <label className="block text-sm text-txt-secondary mb-1.5">确认密码</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-txt-primary placeholder-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500"
                  placeholder="再次输入新密码"
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
                    重置中...
                  </span>
                ) : '重置密码'}
              </button>

              <button
                type="button"
                onClick={() => { setStep(1); setError(''); setToken(''); }}
                className="w-full py-2 text-txt-muted hover:text-txt-primary text-sm transition-colors"
              >
                返回
              </button>
            </form>
          )}

          {/* Step 3: 成功 */}
          {step === 3 && (
            <div className="text-center space-y-4">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/10 border border-green-500/30 mb-2">
                <span className="text-3xl">✅</span>
              </div>
              <p className="text-txt-primary font-medium">密码重置成功</p>
              <p className="text-txt-muted text-sm">已自动登录，正在跳转...</p>
              <button
                onClick={() => window.location.reload()}
                className="w-full py-2.5 bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 text-white font-medium rounded-xl transition-all shadow-lg shadow-brand-500/25"
              >
                进入系统
              </button>
            </div>
          )}
        </div>

        {/* 返回登录 */}
        <button
          onClick={onBack}
          className="block mx-auto mt-6 text-sm text-txt-muted hover:text-brand-400 transition-colors"
        >
          ← 返回登录
        </button>

        <p className="text-center text-xs text-txt-muted mt-4">
          EchoFlow AI v1.4 — AI Native 内容增长运营系统
        </p>
      </div>
    </div>
  );
}
