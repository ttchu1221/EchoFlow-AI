import { useState, useEffect } from 'react';
import { getHistory, deleteHistory } from '../api/client';
import DashboardChart, { NEON_COLORS } from './DashboardChart';

const TYPE_LABELS = {
  generate: { label: '标题生成', icon: '✍️', color: 'tag-cyan' },
  optimize: { label: '标题优化', icon: '🔧', color: 'tag-green' },
  trend_analysis: { label: '趋势分析', icon: '📊', color: 'tag-purple' },
  feedback_analysis: { label: '评论分析', icon: '💬', color: 'tag-amber' },
  script_generation: { label: '脚本生成', icon: '📝', color: 'tag-blue' },
  cover_design: { label: '封面设计', icon: '🎨', color: 'tag-red' },
  publish_strategy: { label: '发布策略', icon: '📡', color: 'tag-green' },
  full_pipeline: { label: '全流程', icon: '🚀', color: 'tag-purple' },
  analytics: { label: '数据分析', icon: '📈', color: 'tag-amber' },
};

export default function HistoryPanel() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  const loadHistory = async () => {
    setLoading(true);
    try { const data = await getHistory(50); setRecords(data.history || []); }
    catch (e) { alert(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadHistory(); }, []);

  const handleDelete = async (id) => {
    try { await deleteHistory(id); setRecords(records.filter((r) => r.id !== id)); }
    catch (e) { alert(e.message); }
  };

  const formatTime = (ts) => {
    try { return new Date(ts).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }); }
    catch { return ts; }
  };

  /* ── 类型分布饼图 ──────────────────────────────── */
  const typePieOption = records.length > 0 ? {
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '50%'],
      data: (() => {
        const counts = {};
        records.forEach(r => { counts[r.type] = (counts[r.type] || 0) + 1; });
        return Object.entries(counts).map(([k, v], i) => ({
          value: v,
          name: TYPE_LABELS[k]?.label || k,
          itemStyle: { color: NEON_COLORS[i % NEON_COLORS.length] },
        }));
      })(),
      label: { show: true, color: '#94a3b8', fontSize: 11, formatter: '{b}\n{c}' },
      emphasis: { label: { fontSize: 13, fontWeight: 'bold', color: '#e2e8f0' } },
      itemStyle: { borderColor: '#0d1117', borderWidth: 3 },
    }],
    tooltip: { trigger: 'item' },
  } : null;

  /* ── 时间趋势柱状图（按天）────────────────── */
  const dailyBarOption = records.length > 0 ? {
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: (() => {
        const days = {};
        records.forEach(r => {
          const d = r.created_at?.slice(0, 10) || '未知';
          days[d] = (days[d] || 0) + 1;
        });
        return Object.keys(days).slice(-14);
      })(),
      axisLabel: { color: '#64748b', fontSize: 10, rotate: 30 },
    },
    yAxis: { type: 'value', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.2)', type: 'dashed' } } },
    series: [{
      type: 'bar',
      data: (() => {
        const days = {};
        records.forEach(r => { const d = r.created_at?.slice(0, 10) || '未知'; days[d] = (days[d] || 0) + 1; });
        return Object.entries(days).slice(-14).map(([_, v], i) => ({
          value: v,
          itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#22d3ee' }, { offset: 1, color: '#0891b2' }] }, borderRadius: [6, 6, 0, 0] },
        }));
      })(),
      barWidth: 20,
    }],
    tooltip: { trigger: 'axis' },
  } : null;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold text-txt-bright flex items-center gap-3">
            <span className="w-1 h-6 rounded-full bg-gradient-to-b from-slate-400 to-slate-600" />
            历史记录
          </h2>
          <p className="text-sm text-txt-secondary mt-1">查看所有 AI 生成记录</p>
        </div>
        <button className="btn-ghost text-sm" onClick={loadHistory}>🔄 刷新</button>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <div key={i} className="shimmer h-16 rounded-2xl" />)}
        </div>
      ) : records.length === 0 ? (
        <div className="card p-16 text-center">
          <p className="text-5xl mb-4">📋</p>
          <p className="text-txt-secondary">暂无历史记录，开始使用 AI 功能吧！</p>
        </div>
      ) : (
        <>
          {/* 图表 */}
          {typePieOption && dailyBarOption && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-txt-primary mb-2 flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-purple-400" />
                  类型分布
                </h3>
                <DashboardChart option={typePieOption} height={260} />
              </div>
              <div className="lg:col-span-2 card p-4">
                <h3 className="text-sm font-semibold text-txt-primary mb-2 flex items-center gap-2">
                  <span className="w-1 h-4 rounded-full bg-brand-400" />
                  每日使用趋势
                </h3>
                <DashboardChart option={dailyBarOption} height={260} />
              </div>
            </div>
          )}

          {/* 记录列表 */}
          <div className="card overflow-hidden">
            <div className="px-5 py-3 border-b border-panel-border flex items-center justify-between">
              <h3 className="text-sm font-semibold text-txt-primary">全部记录</h3>
              <span className="text-xs text-txt-muted">{records.length} 条</span>
            </div>
            <div className="divide-y divide-panel-border/50 max-h-[500px] overflow-y-auto">
              {records.map((record) => {
                const typeInfo = TYPE_LABELS[record.type] || { label: record.type, icon: '📄', color: 'tag-gray' };
                const isExpanded = expanded === record.id;
                return (
                  <div key={record.id}>
                    <div
                      className="flex items-center gap-4 px-5 py-3.5 hover:bg-panel-100/30 transition-colors cursor-pointer"
                      onClick={() => setExpanded(isExpanded ? null : record.id)}
                    >
                      <span className="text-lg">{typeInfo.icon}</span>
                      <span className={`tag ${typeInfo.color}`}>{typeInfo.label}</span>
                      <span className="flex-1 text-sm text-txt-secondary truncate">{record.topic || record.title || '-'}</span>
                      <span className="text-xs text-txt-muted flex-shrink-0">{formatTime(record.created_at)}</span>
                      <button className="text-txt-muted hover:text-red-400 transition-colors p-1"
                        onClick={(e) => { e.stopPropagation(); handleDelete(record.id); }} title="删除">✕</button>
                    </div>
                    {isExpanded && (
                      <div className="px-5 pb-4 animate-fade-in">
                        <pre className="text-xs text-txt-secondary bg-panel-100 rounded-xl p-4 max-h-60 overflow-auto whitespace-pre-wrap border border-panel-border">
                          {JSON.stringify(record.data, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
