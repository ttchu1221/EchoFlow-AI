import { Bars3Icon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { useState, useEffect, useRef } from 'react';
import { getProviders } from '../api/client';
import { getLLMProvider, setLLMProvider } from '../utils/llmProvider';

export default function Header({ onMenuToggle, sidebarOpen, user, onLogout }) {
  const [showMenu, setShowMenu] = useState(false);
  const [showLLM, setShowLLM] = useState(false);
  const [providers, setProviders] = useState([]);
  const [selected, setSelected] = useState(getLLMProvider());
  const llmRef = useRef(null);

  const roleLabels = { admin: '管理员', editor: '编辑', reviewer: '审核员', viewer: '只读' };

  // 加载可用提供商
  useEffect(() => {
    getProviders()
      .then((data) => {
        setProviders(data.providers || []);
        // 首次访问时自动选中后端默认值
        if (!getLLMProvider() && data.default) {
          const match = (data.providers || []).find((p) => p.id === data.default);
          if (match) {
            setLLMProvider(data.default);
            setSelected(data.default);
          }
        }
      })
      .catch(() => {});
  }, []);

  // 点击外部关闭 LLM 下拉
  useEffect(() => {
    const handler = (e) => {
      if (llmRef.current && !llmRef.current.contains(e.target)) setShowLLM(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelectProvider = (id) => {
    setLLMProvider(id);
    setSelected(id);
    setShowLLM(false);
  };

  const currentProvider = providers.find((p) => p.id === selected);

  return (
    <header className="sticky top-0 z-10 flex items-center h-16 px-6 bg-panel/80 backdrop-blur-xl border-b border-panel-border">
      <button
        onClick={onMenuToggle}
        className="lg:hidden p-2 -ml-2 rounded-xl text-txt-muted hover:bg-panel-100 transition-colors"
      >
        <Bars3Icon className="w-5 h-5" />
      </button>

      <div className="flex items-center gap-3 ml-2 lg:ml-0">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
          </span>
          <span className="text-sm text-txt-secondary">系统运行中</span>
        </div>
      </div>

      <div className="flex items-center gap-3 ml-auto">
        {/* LLM 提供商选择器 */}
        <div className="relative hidden sm:block" ref={llmRef}>
          <button
            onClick={() => setShowLLM(!showLLM)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-panel-100 border border-panel-border hover:border-brand-500/30 transition-colors"
          >
            <span className="text-xs text-txt-muted">LLM</span>
            <span className="text-xs font-medium text-brand-400">
              {currentProvider ? currentProvider.name : '自动'}
            </span>
            {currentProvider && (
              <span className="text-[10px] text-txt-muted">{currentProvider.model}</span>
            )}
            <ChevronDownIcon className={`w-3 h-3 text-txt-muted transition-transform ${showLLM ? 'rotate-180' : ''}`} />
          </button>

          {showLLM && providers.length > 0 && (
            <div className="absolute right-0 top-full mt-2 w-56 bg-panel-50 border border-panel-border rounded-xl shadow-xl overflow-hidden z-50">
              <div className="px-3 py-2 border-b border-panel-border">
                <span className="text-[10px] text-txt-muted uppercase tracking-wider">选择模型</span>
              </div>
              {providers.map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleSelectProvider(p.id)}
                  className={`w-full px-3 py-2.5 flex items-center justify-between text-left transition-colors ${
                    selected === p.id
                      ? 'bg-brand-500/10 text-brand-400'
                      : 'text-txt-secondary hover:bg-panel-100'
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{p.name}</span>
                    <span className="text-[10px] text-txt-muted">{p.model}</span>
                  </div>
                  {selected === p.id && (
                    <span className="w-2 h-2 rounded-full bg-brand-400" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-panel-100 border border-panel-border">
          <span className="text-xs text-txt-muted">DB</span>
          <span className="text-xs font-medium text-emerald-400">MongoDB</span>
        </div>

        {/* 用户菜单 */}
        {user ? (
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-panel-100 border border-panel-border hover:border-brand-500/30 transition-colors"
            >
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white text-xs font-semibold">
                {(user.display_name || user.username || '?')[0]}
              </div>
              <span className="text-xs text-txt-primary hidden sm:block">{user.display_name || user.username}</span>
              <span className="text-xs text-txt-muted hidden sm:block">({roleLabels[user.role] || user.role})</span>
            </button>

            {showMenu && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-panel-50 border border-panel-border rounded-xl shadow-xl overflow-hidden z-50">
                <div className="px-4 py-3 border-b border-panel-border">
                  <div className="text-sm text-txt-primary font-medium">{user.display_name || user.username}</div>
                  <div className="text-xs text-txt-muted">@{user.username}</div>
                </div>
                <button
                  onClick={() => { setShowMenu(false); onLogout?.(); }}
                  className="w-full px-4 py-2.5 text-left text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  退出登录
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white text-xs font-semibold shadow-neon-cyan">
            AI
          </div>
        )}
      </div>
    </header>
  );
}
