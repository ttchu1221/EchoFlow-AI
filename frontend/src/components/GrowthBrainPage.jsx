import { useState, useEffect } from 'react';
import { getGrowthBrain, getGrowthMemories, getGrowthStats, getActivePrompts, getStrategyMemories } from '../api/client';

export default function GrowthBrainPage() {
  const [brain, setBrain] = useState(null);
  const [memories, setMemories] = useState([]);
  const [stats, setStats] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadBrainData();
  }, []);

  const loadBrainData = async () => {
    try {
      setLoading(true);
      const [brainRes, memRes, statsRes, stratRes, promptRes] = await Promise.allSettled([
        getGrowthBrain(),
        getGrowthMemories(),
        getGrowthStats(),
        getStrategyMemories(),
        getActivePrompts(),
      ]);

      if (brainRes.status === 'fulfilled') setBrain(brainRes.value);
      if (memRes.status === 'fulfilled') setMemories(memRes.value.memories || []);
      if (statsRes.status === 'fulfilled') setStats(statsRes.value);
      if (stratRes.status === 'fulfilled') setStrategies(stratRes.value.strategies || []);
      if (promptRes.status === 'fulfilled') setPrompts(promptRes.value.prompts || []);
    } catch (e) {
      console.error('加载增长大脑失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'overview', label: '🧠 总览', icon: '🧠' },
    { id: 'memories', label: '💾 增长记忆', icon: '💾' },
    { id: 'strategies', label: '📋 策略库', icon: '📋' },
    { id: 'prompts', label: '🔮 Prompt进化', icon: '🔮' },
    { id: 'patterns', label: '🔗 模式发现', icon: '🔗' },
  ];

  if (loading) {
    return (
      <div className="dashboard-container min-h-screen p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white dashboard-glow-text">增长大脑</h1>
          <p className="text-txt-secondary mt-1">加载中...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="shimmer h-48 rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white dashboard-glow-text">增长大脑</h1>
        <p className="text-txt-secondary mt-1">用户记忆 · 爆款规律 · Pattern Memory · 持续进化</p>
      </div>

      {/* Tab 切换 */}
      <div className="flex flex-wrap gap-2 mb-6">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                : 'bg-panel-100 text-txt-secondary border border-panel-border hover:bg-panel-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 总览 */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* 统计卡片 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="dashboard-panel rounded-2xl p-5 text-center">
              <span className="text-3xl">💾</span>
              <p className="text-2xl font-bold text-brand-400 mt-2">{memories.length}</p>
              <p className="text-xs text-txt-muted">增长记忆</p>
            </div>
            <div className="dashboard-panel rounded-2xl p-5 text-center">
              <span className="text-3xl">📋</span>
              <p className="text-2xl font-bold text-emerald-400 mt-2">{strategies.length}</p>
              <p className="text-xs text-txt-muted">策略记录</p>
            </div>
            <div className="dashboard-panel rounded-2xl p-5 text-center">
              <span className="text-3xl">🔮</span>
              <p className="text-2xl font-bold text-purple-400 mt-2">{prompts.length}</p>
              <p className="text-xs text-txt-muted">活跃Prompt</p>
            </div>
            <div className="dashboard-panel rounded-2xl p-5 text-center">
              <span className="text-3xl">🔗</span>
              <p className="text-2xl font-bold text-amber-400 mt-2">{brain?.patterns?.length || 0}</p>
              <p className="text-xs text-txt-muted">发现模式</p>
            </div>
          </div>

          {/* 模式发现 */}
          <div className="dashboard-panel rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">🔗 已发现的增长模式</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(brain?.patterns || []).map((p, i) => (
                <div key={i} className="p-4 rounded-xl bg-panel-100/50 border border-panel-border">
                  <p className="text-sm font-bold text-white mb-2">{p.pattern}</p>
                  <p className="text-sm text-txt-secondary">{p.insight}</p>
                  <div className="mt-3">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-txt-muted">置信度</span>
                      <span className="text-brand-400">{(p.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 bg-panel-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-brand-500 to-brand-400 rounded-full"
                        style={{ width: `${p.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 知识图谱可视化 */}
          <div className="dashboard-panel rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">🌐 知识图谱</h3>
            <div className="flex flex-wrap gap-3 justify-center py-8">
              {['爆款标题', '定价策略', '达人合作', '投放时段', '内容风格', '用户画像', '平台算法', '转化漏斗'].map((node, i) => {
                const sizes = ['text-sm', 'text-base', 'text-lg', 'text-sm', 'text-base', 'text-sm', 'text-lg', 'text-base'];
                const colors = [
                  'text-brand-400', 'text-emerald-400', 'text-purple-400', 'text-amber-400',
                  'text-blue-400', 'text-pink-400', 'text-cyan-400', 'text-red-400',
                ];
                return (
                  <span
                    key={node}
                    className={`px-4 py-2 rounded-xl bg-panel-100/50 border border-panel-border ${sizes[i]} ${colors[i]} font-medium hover:scale-110 transition-transform cursor-default`}
                  >
                    {node}
                  </span>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* 增长记忆 */}
      {activeTab === 'memories' && (
        <div className="space-y-4">
          {memories.length > 0 ? memories.map((m, i) => (
            <div key={i} className="dashboard-panel rounded-2xl p-5">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="text-base font-bold text-white">{m.content_title || `记忆 #${i + 1}`}</h4>
                  <p className="text-xs text-txt-muted mt-1">{m.created_at}</p>
                </div>
                <span className={`tag ${m.outcome === 'success' ? 'tag-green' : 'tag-red'}`}>
                  {m.outcome === 'success' ? '成功' : '失败'}
                </span>
              </div>
              {m.success_factors && (
                <p className="text-sm text-txt-secondary mb-2">成功因素: {m.success_factors}</p>
              )}
              {m.failure_reasons && (
                <p className="text-sm text-txt-secondary mb-2">失败原因: {m.failure_reasons}</p>
              )}
              {m.platform && <span className="tag-cyan">{m.platform}</span>}
            </div>
          )) : (
            <div className="dashboard-panel rounded-2xl p-12 text-center">
              <span className="text-5xl mb-4 block">💾</span>
              <p className="text-lg font-medium text-txt-secondary">暂无增长记忆</p>
              <p className="text-sm text-txt-muted mt-1">使用增长闭环功能后，记忆将自动积累</p>
            </div>
          )}
        </div>
      )}

      {/* 策略库 */}
      {activeTab === 'strategies' && (
        <div className="space-y-4">
          {strategies.length > 0 ? strategies.map((s, i) => (
            <div key={i} className="dashboard-panel rounded-2xl p-5">
              <div className="flex items-start justify-between mb-3">
                <h4 className="text-base font-bold text-white">{s.strategy_name || `策略 #${i + 1}`}</h4>
                <span className={`tag ${s.status === 'active' ? 'tag-green' : 'tag-gray'}`}>
                  {s.status || 'draft'}
                </span>
              </div>
              <p className="text-sm text-txt-secondary">{s.description || s.strategy_content || '暂无描述'}</p>
            </div>
          )) : (
            <div className="dashboard-panel rounded-2xl p-12 text-center">
              <span className="text-5xl mb-4 block">📋</span>
              <p className="text-lg font-medium text-txt-secondary">暂无策略记录</p>
            </div>
          )}
        </div>
      )}

      {/* Prompt 进化 */}
      {activeTab === 'prompts' && (
        <div className="space-y-4">
          {prompts.length > 0 ? prompts.map((p, i) => (
            <div key={i} className="dashboard-panel rounded-2xl p-5">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-xl">🔮</span>
                <div>
                  <h4 className="text-base font-bold text-white">{p.name || `Prompt #${i + 1}`}</h4>
                  <p className="text-xs text-txt-muted">{p.version || 'v1.0'}</p>
                </div>
              </div>
              <pre className="text-sm text-txt-secondary bg-panel-100/50 p-3 rounded-xl overflow-x-auto">
                {p.content || p.template || '暂无内容'}
              </pre>
            </div>
          )) : (
            <div className="dashboard-panel rounded-2xl p-12 text-center">
              <span className="text-5xl mb-4 block">🔮</span>
              <p className="text-lg font-medium text-txt-secondary">暂无活跃 Prompt</p>
            </div>
          )}
        </div>
      )}

      {/* 模式发现 */}
      {activeTab === 'patterns' && (
        <div className="space-y-4">
          {(brain?.patterns || []).length > 0 ? brain.patterns.map((p, i) => (
            <div key={i} className="dashboard-panel rounded-2xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="text-lg font-bold text-white">{p.pattern}</h4>
                  <p className="text-sm text-txt-secondary mt-1">{p.insight}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-brand-400">{(p.confidence * 100).toFixed(0)}%</p>
                  <p className="text-xs text-txt-muted">置信度</p>
                </div>
              </div>
              <div className="h-2 bg-panel-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-brand-500 to-emerald-500 rounded-full transition-all duration-1000"
                  style={{ width: `${p.confidence * 100}%` }}
                />
              </div>
            </div>
          )) : (
            <div className="dashboard-panel rounded-2xl p-12 text-center">
              <span className="text-5xl mb-4 block">🔗</span>
              <p className="text-lg font-medium text-txt-secondary">暂无发现模式</p>
              <p className="text-sm text-txt-muted mt-1">系统将持续学习并发现增长模式</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
