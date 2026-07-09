import { useState, useEffect } from 'react';
import { getAgents, getAgentDetail, executeAgentTask } from '../api/client';

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [executeAction, setExecuteAction] = useState('');

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const result = await getAgents();
      setAgents(result.agents || []);
    } catch (e) {
      console.error('加载Agent失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAgent = async (agentId) => {
    setSelected(agentId);
    try {
      const result = await getAgentDetail(agentId);
      setDetail(result);
    } catch (e) {
      console.error('加载详情失败:', e);
    }
  };

  const handleExecute = async () => {
    if (!selected || !executeAction.trim()) return;
    try {
      setExecuting(true);
      await executeAgentTask(selected, executeAction);
      setExecuteAction('');
      // 刷新详情
      const result = await getAgentDetail(selected);
      setDetail(result);
    } catch (e) {
      console.error('执行失败:', e);
    } finally {
      setExecuting(false);
    }
  };

  const statusColors = {
    active: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    idle: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    busy: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  };

  return (
    <div className="dashboard-container min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white dashboard-glow-text">智能体管理</h1>
        <p className="text-txt-secondary mt-1">7个专业 Agent 协同工作 · 覆盖电商运营全链路</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent 列表 */}
        <div className="lg:col-span-1 space-y-3">
          {loading ? (
            <div className="space-y-3">
              {[1,2,3,4,5,6,7].map(i => (
                <div key={i} className="shimmer h-20 rounded-xl" />
              ))}
            </div>
          ) : (
            agents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => handleSelectAgent(agent.id)}
                className={`w-full text-left p-4 rounded-xl border transition-all duration-200 ${
                  selected === agent.id
                    ? 'bg-brand-500/10 border-brand-500/30 shadow-[0_0_15px_rgba(34,211,238,0.1)]'
                    : 'bg-panel-50 border-panel-border hover:bg-panel-100 hover:border-panel-border'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{agent.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-white truncate">{agent.name}</p>
                    <p className="text-xs text-txt-muted mt-0.5 truncate">{agent.description}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`px-2 py-0.5 rounded-full text-xs border ${statusColors[agent.status] || statusColors.idle}`}>
                      {agent.status}
                    </span>
                    <span className="text-xs text-txt-muted">{agent.tasks_today} 任务</span>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Agent 详情 */}
        <div className="lg:col-span-2">
          {detail ? (
            <div className="space-y-6">
              {/* 头部信息 */}
              <div className="dashboard-panel rounded-2xl p-6">
                <div className="flex items-center gap-4 mb-6">
                  <span className="text-4xl">{detail.icon}</span>
                  <div>
                    <h2 className="text-2xl font-bold text-white">{detail.name}</h2>
                    <p className="text-txt-secondary">{detail.description}</p>
                  </div>
                </div>

                {/* 指标卡片 */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl bg-panel-100/50 text-center">
                    <p className="text-2xl font-bold text-brand-400">{detail.tasks_today}</p>
                    <p className="text-xs text-txt-muted mt-1">今日任务</p>
                  </div>
                  <div className="p-4 rounded-xl bg-panel-100/50 text-center">
                    <p className="text-2xl font-bold text-emerald-400">{(detail.success_rate * 100).toFixed(0)}%</p>
                    <p className="text-xs text-txt-muted mt-1">成功率</p>
                  </div>
                  <div className="p-4 rounded-xl bg-panel-100/50 text-center">
                    <p className="text-2xl font-bold text-amber-400">{detail.avg_response_time}</p>
                    <p className="text-xs text-txt-muted mt-1">平均响应</p>
                  </div>
                </div>
              </div>

              {/* 能力标签 */}
              <div className="dashboard-panel rounded-2xl p-6">
                <h3 className="text-lg font-bold text-white mb-4">🎯 核心能力</h3>
                <div className="flex flex-wrap gap-2">
                  {detail.capabilities.map((cap) => (
                    <span key={cap} className="tag-cyan">{cap}</span>
                  ))}
                </div>
              </div>

              {/* 手动执行 */}
              <div className="dashboard-panel rounded-2xl p-6">
                <h3 className="text-lg font-bold text-white mb-4">⚡ 手动执行</h3>
                <div className="flex gap-3">
                  <input
                    type="text"
                    className="input flex-1"
                    placeholder="输入任务描述..."
                    value={executeAction}
                    onChange={(e) => setExecuteAction(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
                  />
                  <button
                    onClick={handleExecute}
                    disabled={!executeAction.trim() || executing}
                    className="btn-primary"
                  >
                    {executing ? '执行中...' : '执行'}
                  </button>
                </div>
              </div>

              {/* 最近任务 */}
              <div className="dashboard-panel rounded-2xl p-6">
                <h3 className="text-lg font-bold text-white mb-4">📋 最近任务</h3>
                <div className="space-y-3">
                  {detail.recent_tasks.map((task, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-panel-100/50">
                      <span className={`w-2 h-2 rounded-full ${task.status === 'success' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                      <span className="text-sm text-txt-primary flex-1">{task.action}</span>
                      <span className="text-xs text-txt-muted">{task.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="dashboard-panel rounded-2xl p-12 flex flex-col items-center justify-center">
              <span className="text-6xl mb-4">🤖</span>
              <p className="text-lg font-medium text-txt-secondary">选择一个 Agent 查看详情</p>
              <p className="text-sm text-txt-muted mt-1">7个专业Agent覆盖电商运营全链路</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
