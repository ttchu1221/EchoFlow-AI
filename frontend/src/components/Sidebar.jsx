import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

export default function Sidebar({ items, groups, active, onSelect, open, onToggle }) {
  const isDashboard = active === 'dashboard';

  return (
    <>
      {/* 移动端遮罩 */}
      {open && !isDashboard && (
        <div
          className="fixed inset-0 z-[35] bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onToggle}
        />
      )}

      <aside
        className={`
          ${isDashboard
            ? 'fixed inset-y-0 left-0 z-40 w-64'
            : 'fixed inset-y-0 left-0 z-30 lg:static lg:z-auto'
          }
          flex flex-col bg-panel-50/90 backdrop-blur-xl border-r border-panel-border
          transition-[width,transform] duration-300 ease-in-out
          ${isDashboard
            ? (open ? 'translate-x-0' : '-translate-x-full')
            : (open
                ? 'w-64 translate-x-0 lg:w-64'
                : 'w-0 -translate-x-full lg:w-20 lg:translate-x-0'
              )
          }
          ${!isDashboard && !open ? 'lg:overflow-hidden' : ''}
        `}
      >
        {/* Logo */}
        <div className={`flex items-center h-16 px-4 border-b border-panel-border min-h-[64px] ${!open && 'lg:justify-center lg:px-2'}`}>
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold text-lg flex-shrink-0 shadow-neon-cyan">
              E
            </div>
            {open && (
              <div className="min-w-0">
                <h1 className="text-txt-bright font-semibold text-sm tracking-tight truncate">EchoFlow AI</h1>
                <p className="text-txt-muted text-xs truncate">智能内容增长系统</p>
              </div>
            )}
          </div>
        </div>

        {/* 导航 */}
        <nav className={`flex-1 overflow-y-auto py-4 ${open ? 'px-3' : 'lg:px-2'}`}>
          {groups.map((group) => (
            <div key={group} className="mb-4">
              {open && (
                <p className="px-3 mb-2 text-[11px] font-semibold text-txt-muted/60 uppercase tracking-wider">
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
                          ${open ? 'px-3 py-2.5' : 'lg:justify-center lg:px-2 lg:py-3'}
                          ${isActive
                            ? 'bg-brand-500/15 text-brand-300 border border-brand-500/20 shadow-sm'
                            : 'text-txt-secondary hover:bg-panel-100 hover:text-txt-primary border border-transparent'
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
                          <span className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400 shadow-neon-cyan" />
                        )}
                      </button>
                    );
                  })}
              </div>
            </div>
          ))}
        </nav>

        {/* 折叠按钮 */}
        {!isDashboard && (
          <div className="hidden lg:flex items-center justify-center h-12 border-t border-panel-border">
            <button
              onClick={onToggle}
              className="p-1.5 rounded-lg text-txt-muted hover:text-txt-primary hover:bg-panel-100 transition-colors"
            >
              {open ? (
                <ChevronLeftIcon className="w-4 h-4" />
              ) : (
                <ChevronRightIcon className="w-4 h-4" />
              )}
            </button>
          </div>
        )}
      </aside>
    </>
  );
}
