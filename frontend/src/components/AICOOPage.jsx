import { useState, useRef, useEffect } from 'react';
import { cooDispatch, executeCooTask, getCooTask, cooAnalyze, cooChat } from '../api/client';

const GOAL_PRESETS = [
  { label: 'GMV增长', goal: '本周GMV提升30%', icon: '📈' },
  { label: '内容推广', goal: '推广新品SKU，提升曝光量', icon: '📢' },
  { label: '达人合作', goal: '寻找3位高转化达人进行合作', icon: '🤝' },
  { label: '广告优化', goal: '优化广告投放，降低CPA提升ROI', icon: '📊' },
];

export default function AICOOPage() {
  const [goal, setGoal] = useState('');
  const [task, setTask] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatting, setChatting] = useState(false);
  const [activeTab, setActiveTab] = useState('dispatch');
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleDispatch = async () => {
    if (!goal.trim()) return;
    try {
      setExecuting(true);
      const result = await cooDispatch(goal);
      setTask({ ...result, goal, progress: [] });
      // 轮询任务状态，每 3 秒更新一次
      const pollInterval = setInterval(async () => {
        try {
          const updated = await getCooTask(result.task_id);
          setTask(updated);
          if (updated.status === 'completed' || updated.status === 'failed') {
            clearInterval(pollInterval);
          }
        } catch { clearInterval(pollInterval); }
      }, 3000);
      // 5 分钟后停止轮询
      setTimeout(() => clearInterval(pollInterval), 5 * 60 * 1000);
    } catch (e) {
      console.error('调度失败:', e);
    } finally {
      setExecuting(false);
    }
  };

  const handleExecute = async () => {
    if (!task?.task_id) return;
    try {
      setExecuting(true);
      const result = await executeCooTask(task.task_id);
      setTask(prev => ({ ...prev, ...result }));
      // 轮询任务状态
      const tid = result.task_id || task.task_id;
      const pollInterval = setInterval(async () => {
        try {
          const updated = await getCooTask(tid);
          setTask(updated);
          if (updated.status === 'completed' || updated.status === 'failed') {
            clearInterval(pollInterval);
          }
        } catch { clearInterval(pollInterval); }
      }, 3000);
      setTimeout(() => clearInterval(pollInterval), 5 * 60 * 1000);
    } catch (e) {
      console.error('执行失败:', e);
    } finally {
      setExecuting(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim() || chatting) return;
    const userMsg = chatInput.trim();
    setChatInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }, { role: 'assistant', content: '' }]);
    setChatting(true);

    try {
      await cooChat(userMsg, (fullContent) => {
        // 流式更新最后一条 assistant 消息
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: fullContent };
          return updated;
        });
      });
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === 'assistant' && !last.content) {
          last.content = '处理失败，请重试';
        } else {
          updated.push({ role: 'assistant', content: '处理失败，请重试' });
        }
        return updated;
      });
    } finally {
      setChatting(false);
    }
  };

  const getAgentIcon = (agentId) => {
    const icons = { market: '🔍', product: '📦', content: '✍️', creator: '👤', ads: '📊', analytics: '📈', memory: '🧠' };
    return icons[agentId] || '🤖';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-emerald-500';
      case 'running': return 'bg-brand-500 animate-pulse';
      case 'failed': return 'bg-red-500';
      case 'pending': return 'bg-slate-500';
      default: return 'bg-slate-500';
    }
  };

  return (
    <div className="dashboard-container min-h-screen p-6">
      {/* 标题 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white dashboard-glow-text">AI COO 调度中心</h1>
        <p className="text-txt-secondary mt-1">一句话驱动多Agent协作 · 自动拆解运营目标</p>
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-2 mb-6">
        {[
          { id: 'dispatch', label: '🎯 任务调度', icon: '🎯' },
          { id: 'chat', label: '💬 COO 对话', icon: '💬' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                : 'bg-panel-100 text-txt-secondary hover:bg-panel-200 border border-panel-border'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'dispatch' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左侧：目标输入 */}
          <div className="space-y-6">
            {/* 目标输入卡片 */}
            <div className="dashboard-panel rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">📝 输入运营目标</h3>
              <textarea
                className="textarea h-32 mb-4"
                placeholder="例如：本周GMV提升30%、推广新品SKU、寻找高转化达人..."
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
              />
              <div className="flex flex-wrap gap-2 mb-4">
                {GOAL_PRESETS.map((p) => (
                  <button
                    key={p.label}
                    onClick={() => setGoal(p.goal)}
                    className="px-3 py-1.5 rounded-lg text-xs bg-panel-200 text-txt-secondary hover:bg-panel-300 hover:text-txt-primary transition-colors"
                  >
                    {p.icon} {p.label}
                  </button>
                ))}
              </div>
              <button
                onClick={handleDispatch}
                disabled={!goal.trim() || executing}
                className="btn-primary w-full"
              >
                {executing ? '分析中...' : '🚀 AI COO 分析拆解'}
              </button>
            </div>

            {/* 历史任务 */}
            <div className="dashboard-panel rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">📜 历史目标</h3>
              <div className="space-y-2 text-sm text-txt-secondary">
                <p className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  GMV增长30% — 已完成
                </p>
                <p className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  推广SKU23 — 已完成
                </p>
                <p className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
                  达人合作优化 — 执行中
                </p>
              </div>
            </div>
          </div>

          {/* 右侧：任务拆解 */}
          <div className="dashboard-panel rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">🔗 任务拆解</h3>
            {task ? (
              <div>
                <div className="mb-4 p-4 rounded-xl bg-brand-500/10 border border-brand-500/20">
                  <p className="text-sm text-brand-300 font-medium">目标</p>
                  <p className="text-white mt-1">{task.goal || goal || '—'}</p>
                </div>

                {/* 步骤列表 */}
                <div className="space-y-3 mb-6">
                  {(task.breakdown || []).map((step, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-panel-100/50">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${getStatusColor(step.status)}`}>
                        {step.status === 'completed' ? (
                          <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        ) : (
                          <span className="text-xs text-white font-bold">{step.step || i + 1}</span>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span>{getAgentIcon(step.agent)}</span>
                          <span className="text-sm font-medium text-white">{step.action || step.description || '执行步骤'}</span>
                        </div>
                        <p className="text-xs text-txt-muted mt-1">
                          {step.agent} Agent · {step.status === 'completed' ? '✅ 已完成' : step.status === 'running' ? '⏳ 执行中' : step.status === 'failed' ? '❌ 失败' : `预计 ${step.estimated_time || '—'}`}
                        </p>
                        {step.result && step.status === 'completed' && (
                          <p className="text-xs text-txt-secondary mt-1 line-clamp-3">{typeof step.result === 'string' ? step.result.slice(0, 200) : JSON.stringify(step.result).slice(0, 200)}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* 执行按钮 */}
                {task.status !== 'completed' && task.status !== 'failed' && (
                  <button
                    onClick={handleExecute}
                    disabled={executing}
                    className="btn-primary w-full"
                  >
                    {executing ? '执行中...' : '⚡ 执行全部任务'}
                  </button>
                )}

                {/* 执行进度日志 */}
                {task.progress && task.progress.length > 0 && (
                  <div className="mt-4 p-3 rounded-xl bg-panel-100/50 max-h-32 overflow-y-auto">
                    <p className="text-xs text-txt-muted mb-2">执行日志</p>
                    {task.progress.map((p, i) => (
                      <p key={i} className="text-xs text-txt-secondary">{p}</p>
                    ))}
                  </div>
                )}

                {task.status === 'completed' && task.result && (
                  <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <p className="text-sm text-emerald-300 font-medium">✅ 执行完成</p>
                    <p className="text-txt-secondary text-sm mt-1">{typeof task.result === 'string' ? task.result : (task.result.summary || task.result.message || JSON.stringify(task.result))}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-txt-muted">
                <span className="text-5xl mb-4">🎯</span>
                <p className="text-lg font-medium">输入运营目标开始拆解</p>
                <p className="text-sm mt-1">AI COO 将自动规划多Agent协作方案</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* COO 对话模式 */
        <div className="dashboard-panel rounded-2xl p-6 max-w-4xl mx-auto">
          <div className="h-[500px] flex flex-col">
            {/* 消息区域 */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-txt-muted">
                  <span className="text-5xl mb-4">🤖</span>
                  <p className="text-lg font-medium">AI COO 为您服务</p>
                  <p className="text-sm mt-1">询问任何运营问题，获取专业建议</p>
                  <div className="flex flex-wrap gap-2 mt-6">
                    {['今日数据如何？', '如何提升GMV？', '广告怎么优化？', '达人合作建议'].map(q => (
                      <button
                        key={q}
                        onClick={() => { setChatInput(q); }}
                        className="px-3 py-1.5 rounded-lg text-xs bg-panel-200 text-txt-secondary hover:bg-panel-300 transition-colors"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-4 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-brand-500/20 text-white'
                      : 'bg-panel-100 text-txt-primary'
                  }`}>
                    {msg.role === 'assistant' && (
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">🤖</span>
                        <span className="text-xs text-brand-400 font-medium">AI COO</span>
                      </div>
                    )}
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              {chatting && (
                <div className="flex justify-start">
                  <div className="bg-panel-100 p-4 rounded-2xl">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🤖</span>
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" />
                        <span className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <span className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* 输入区域 */}
            <div className="flex gap-3">
              <input
                type="text"
                className="input flex-1"
                placeholder="向 AI COO 提问..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleChat()}
              />
              <button
                onClick={handleChat}
                disabled={!chatInput.trim() || chatting}
                className="btn-primary"
              >
                发送
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
