import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

export default function Sidebar({ items, groups, active, onSelect, open, onToggle }) {
  return (
    <>
      {/* 移动端遮罩 */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/30 backdrop-blur-sm lg:hidden"
          onClick={onToggle}
        />
      )}

      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-30
          flex flex-col bg-sidebar-bg
          transition-all duration-300 ease-in-out
          ${open ? 'w-64 translate-x-0' : 'w-0 -translate-x-full lg:w-20 lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className={`flex items-center h-16 px-4 border-b border-white/5 ${!open && 'lg:justify-center'}`}>
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold text-lg flex-shrink-0 shadow-lg shadow-brand-500/20">
              E
            </div>
            {open && (
              <div className="min-w-0">
                <h1 className="text-white font-semibold text-sm tracking-tight truncate">EchoFlow AI</h1>
                <p className="text-sidebar-text text-xs truncate">智能内容运营平台</p>
              </div>
            )}
          </div>
        </div>

        {/* 导航 */}
        <nav className={`flex-1 overflow-y-auto py-4 ${open ? 'px-3' : 'px-2'}`}>
          {groups.map((group) => (
            <div key={group} className="mb-4">
              {open && (
                <p className="px-3 mb-2 text-[11px] font-semibold text-sidebar-text/50 uppercase tracking-wider">
                  {group}
                </p>
              )}
              <div className="space-y-0.5">
                {items
                  .filter((item) => item.group === group)
                  .map((item) => {
                    const isActive = active === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => onSelect(item.id)}
                        className={`
                          w-full flex items-center gap-3 rounded-xl text-sm font-medium
                          transition-all duration-150
                          ${open ? 'px-3 py-2.5' : 'justify-center px-2 py-3'}
                          ${isActive
                            ? 'bg-sidebar-active text-white shadow-sm'
                            : 'text-sidebar-text hover:bg-sidebar-hover hover:text-sidebar-bright'
                          }
                        `}
                        title={item.label}
                      >
                        <span className={`text-base flex-shrink-0 ${isActive ? 'scale-110' : ''} transition-transform`}>
                          {item.icon}
                        </span>
                        {open && (
                          <span className="truncate">{item.label}</span>
                        )}
                        {open && isActive && (
                          <span className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400" />
                        )}
                      </button>
                    );
                  })}
              </div>
            </div>
          ))}
        </nav>

        {/* 折叠按钮 */}
        <div className="hidden lg:flex items-center justify-center h-12 border-t border-white/5">
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg text-sidebar-text hover:text-white hover:bg-sidebar-hover transition-colors"
          >
            {open ? (
              <ChevronLeftIcon className="w-4 h-4" />
            ) : (
              <ChevronRightIcon className="w-4 h-4" />
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
