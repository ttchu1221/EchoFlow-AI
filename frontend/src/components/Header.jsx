import { Bars3Icon } from '@heroicons/react/24/outline';

export default function Header({ onMenuToggle, sidebarOpen }) {
  return (
    <header className="sticky top-0 z-10 flex items-center h-16 px-6 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <button
        onClick={onMenuToggle}
        className="lg:hidden p-2 -ml-2 rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
      >
        <Bars3Icon className="w-5 h-5" />
      </button>

      <div className="flex items-center gap-3 ml-2 lg:ml-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-soft" />
          <span className="text-sm text-gray-500">系统运行中</span>
        </div>
      </div>

      <div className="flex items-center gap-3 ml-auto">
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-50 border border-gray-100">
          <span className="text-xs text-gray-400">LLM</span>
          <span className="text-xs font-medium text-gray-600">Mimo v2.5 Pro</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white text-xs font-semibold shadow-sm">
          AI
        </div>
      </div>
    </header>
  );
}
