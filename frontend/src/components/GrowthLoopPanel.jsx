import { useState, useEffect } from 'react';
import { runGrowthLoop, getGrowthMemories, getGrowthStats, getActivePrompts, createGrowthMemory } from '../api/client';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

export default function GrowthLoopPanel() {
  const [creatorId, setCreatorId] = useState('default');
  const [platform, setPlatform] = useState('xiaohongshu');
  const [currentStrategy, setCurrentStrategy] = useState('');
  const [recentMetrics, setRecentMetrics] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // 记忆数据
  const [memories, setMemories] = useState([]);
  const [stats, setStats] = useState(null);
  const [prompts, setPrompts] = useState([]);
  const [showMemoryForm, setShowMemoryForm] = useState(false);
  const [memoryForm, setMemoryForm] = useState({
    content_title: '', outcome: 'good', metrics_text: '', success_factors_text: '', failure_reasons_text: '',
  });

  useEffect(() => {
    loadData();
  }, [creatorId]);

  const loadData = async () => {
    try {
      const [memoriesData, statsData, promptsData] = await Promise.all([
        getGrowthMemories({ creator_id: creatorId, limit: 10 }),
        getGrowthStats(creatorId),
        getActivePrompts(creatorId),
      ]);
      setMemories(memoriesData.memories || []);
      setStats(statsData);
      setPrompts(promptsData.prompts || []);
    } catch (e) {
      console.error('加载数据失败:', e);
    }
  };

  const handleRunLoop = async () => {
    setLoading(true);
    try {
      let metrics = {};
      if (recentMetrics.trim()) {
        try { metrics = JSON.parse(recentMetrics); } catch { metrics = { raw: recentMetrics }; }
      }
      const data = await runGrowthLoop({
        creator_id: creatorId,
        platform,
        recent_metrics: metrics,
        current_strategy: currentStrategy,
      });
      setResult(data);
      loadData();
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveMemory = async () => {
    try {
      let metrics = {};
      if (memoryForm.metrics_text.trim()) {
        try { metrics = JSON.parse(memoryForm.metrics_text); } catch { metrics = { raw: memoryForm.metrics_text }; }
      }
      await createGrowthMemory({
        creator_id: creatorId,
        platform,
        content_title: memoryForm.content_title,
        outcome: memoryForm.outcome,
        metrics,
        success_factors: memoryForm.success_factors_text.split('，').map(s => s.trim()).filter(Boolean),
        failure_reasons: memoryForm.failure_reasons_text.split('，').map(s => s.trim()).filter(Boolean),
      });
      setShowMemoryForm(false);
      setMemoryForm({ content_title: '', outcome: 'good', metrics_text: '', success_factors_text: '', failure_reasons_text: '' });
      loadData();
    } catch (e) {
      alert(e.message);
    }
  };

  const outcomeBadge = (o) => {
    const map = { viral: '🔥 爆款', good: '👍 良好', average: '😐 一般', poor: '👎 差' };
    const colorMap = { viral: 'tag-red', good: 'tag-green', average: 'tag-gray', poor: 'tag-amber' };
    return <span className={colorMap[o] || 'tag-gray'}>{map[o] || o}</span>;
  };

  const agentLabel = (a) => {
    const map = { topic: '选题', script: '脚本', hook: '钩子', cover: '封面', publish: '发布', trend: '趋势' };
    return map[a] || a;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">🔄 增长反馈闭环</h2>
        <p className="text-sm text-gray-500 mt-1">核心竞争力 — 分析结果自动优化策略和 Prompt，形成增长飞轮</p>
      </div>

      {/* 增长统计 */}
      {stats && stats.total > 0 && (
        <div className="card-flat p-4">
          <div className="flex items-center gap-6 flex-wrap">
            <div className="text-center">
              <div className="text-xl font-bold text-gray-900">{stats.total}</div>
              <div className="text-xs text-gray-500">总记录</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-red-500">{stats.viral}</div>
              <div className="text-xs text-gray-500">爆款</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-amber-500">{stats.viral_rate}%</div>
              <div className="text-xs text-gray-500">爆款率</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-emerald-500">{stats.success_rate}%</div>
              <div className="text-xs text-gray-500">成功率</div>
            </div>
            <div className="flex-1" />
            <button className="btn-secondary text-sm" onClick={() => setShowMemoryForm(true)}>
              + 记录内容表现
            </button>
          </div>
        </div>
      )}

      {/* 记录内容表现表单 */}
      {showMemoryForm && (
        <div className="card p-6 border-2 border-brand-200 animate-fade-in">
          <h3 className="font-semibold text-gray-900 mb-4">📝 记录内容表现</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">内容标题</label>
              <input className="input" value={memoryForm.content_title} onChange={(e) => setMemoryForm(f => ({ ...f, content_title: e.target.value }))} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">表现结果</label>
              <select className="select" value={memoryForm.outcome} onChange={(e) => setMemoryForm(f => ({ ...f, outcome: e.target.value }))}>
                <option value="viral">🔥 爆款</option>
                <option value="good">👍 良好</option>
                <option value="average">😐 一般</option>
                <option value="poor">👎 差</option>
              </select>
            </div>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">表现数据（JSON 或文本）</label>
            <textarea className="input min-h-[60px]" placeholder='如：{"views": 10000, "likes": 500}' value={memoryForm.metrics_text} onChange={(e) => setMemoryForm(f => ({ ...f, metrics_text: e.target.value }))} />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">成功因素（逗号分隔）</label>
              <input className="input" placeholder="如：标题吸引人，内容实用" value={memoryForm.success_factors_text} onChange={(e) => setMemoryForm(f => ({ ...f, success_factors_text: e.target.value }))} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">失败原因（逗号分隔）</label>
              <input className="input" placeholder="如：封面不够吸引" value={memoryForm.failure_reasons_text} onChange={(e) => setMemoryForm(f => ({ ...f, failure_reasons_text: e.target.value }))} />
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn-primary text-sm" onClick={handleSaveMemory}>保存</button>
            <button className="btn-secondary text-sm" onClick={() => setShowMemoryForm(false)}>取消</button>
          </div>
        </div>
      )}

      {/* 运行增长闭环 */}
      <div className="card p-6 space-y-5">
        <h3 className="font-semibold text-gray-900">运行一轮增长闭环</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">创作者 ID</label>
            <input className="input" value={creatorId} onChange={(e) => setCreatorId(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">当前策略描述（可选）</label>
          <textarea className="input min-h-[60px]" placeholder="描述你当前的内容策略..." value={currentStrategy} onChange={(e) => setCurrentStrategy(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">近期表现数据（JSON，可选）</label>
          <textarea className="input min-h-[60px]" placeholder='如：{"avg_views": 5000, "avg_likes": 200, "posting_frequency": "每日1次"}' value={recentMetrics} onChange={(e) => setRecentMetrics(e.target.value)} />
        </div>
        <button className="btn-primary w-full sm:w-auto" onClick={handleRunLoop} disabled={loading}>
          {loading ? '🔄 闭环分析中...' : '🔄 启动增长闭环'}
        </button>
      </div>

      {/* 加载状态 */}
      {loading && (
        <div className="card p-8 text-center">
          <div className="inline-block w-8 h-8 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mb-3" />
          <p className="text-gray-500">增长闭环正在分析数据、优化策略中...</p>
        </div>
      )}

      {/* 闭环结果 */}
      {result && !loading && (
        <div className="space-y-5 animate-fade-in">
          {/* 表现诊断 */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">📋 表现诊断</h3>
              <span className="tag-blue">置信度 {Math.round((result.confidence_score || 0) * 100)}%</span>
            </div>
            <p className="text-gray-700 leading-relaxed">{result.performance_diagnosis}</p>
          </div>

          {/* 策略调整 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🔧 策略调整建议</h3>
            <ul className="space-y-2">
              {(result.strategy_adjustments || []).map((s, i) => (
                <li key={i} className="flex items-start gap-2 p-2 rounded bg-emerald-50 text-sm text-emerald-800">
                  <span className="font-bold">{i + 1}.</span> {s}
                </li>
              ))}
            </ul>
          </div>

          {/* Prompt 优化 */}
          {result.prompt_optimizations && result.prompt_optimizations.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">⚡ Prompt 优化建议</h3>
              <div className="space-y-4">
                {result.prompt_optimizations.map((p, i) => (
                  <div key={i} className="p-4 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="tag-purple">{agentLabel(p.target_agent)}智能体</span>
                      <span className="text-xs text-gray-500">{p.change_reason}</span>
                    </div>
                    {p.original_prompt_hint && (
                      <div className="mb-2">
                        <span className="text-xs font-medium text-red-600">原 Prompt：</span>
                        <p className="text-sm text-gray-600 bg-red-50 p-2 rounded mt-1">{p.original_prompt_hint}</p>
                      </div>
                    )}
                    {p.optimized_prompt_hint && (
                      <div className="mb-2">
                        <span className="text-xs font-medium text-emerald-600">优化后：</span>
                        <p className="text-sm text-gray-600 bg-emerald-50 p-2 rounded mt-1">{p.optimized_prompt_hint}</p>
                      </div>
                    )}
                    {p.expected_impact && (
                      <p className="text-xs text-blue-600">💡 预期效果：{p.expected_impact}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 下一步行动 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 下一步行动</h3>
            <ul className="space-y-2">
              {(result.next_actions || []).map((a, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-brand-500 font-bold">▸</span> {a}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* 增长记忆列表 */}
      {memories.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📚 增长记忆</h3>
          <div className="space-y-2">
            {memories.map((m, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 text-sm">
                {outcomeBadge(m.outcome)}
                <span className="font-medium text-gray-900 flex-1 truncate">{m.content_title || '未命名'}</span>
                <span className="text-xs text-gray-400">{m.platform}</span>
                <span className="text-xs text-gray-400">{m.created_at?.slice(0, 10)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 活跃 Prompt 版本 */}
      {prompts.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🧬 活跃 Prompt 版本</h3>
          <div className="space-y-2">
            {prompts.map((p, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-purple-50 text-sm">
                <span className="tag-purple">{p.prompt_version || 'v?'}</span>
                <span className="font-medium text-gray-900">{p.strategy_name}</span>
                <span className="text-xs text-gray-500">{agentLabel(p.target_agent)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
