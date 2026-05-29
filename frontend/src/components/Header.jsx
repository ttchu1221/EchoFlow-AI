import { Bars3Icon } from '@heroicons/react/24/outline';

export default function Header({ onMenuToggle, sidebarOpen }) {
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
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-panel-100 border border-panel-border">
          <span className="text-xs text-txt-muted">LLM</span>
          <span className="text-xs font-medium text-brand-400">Mimo v2.5 Pro</span>
        </div>
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-panel-100 border border-panel-border">
          <span className="text-xs text-txt-muted">DB</span>
          <span className="text-xs font-medium text-emerald-400">MongoDB</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white text-xs font-semibold shadow-neon-cyan">
          AI
        </div>
      </div>
    </header>
  );
}
