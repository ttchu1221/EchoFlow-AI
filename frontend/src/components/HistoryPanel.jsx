import { useState, useEffect } from 'react';
import { getHistory, deleteHistory } from '../api/client';

const TYPE_LABELS = {
  generate: { label: '标题生成', icon: '✍️', color: 'tag-blue' },
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
    try {
      const data = await getHistory(50);
      setRecords(data.history || []);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadHistory(); }, []);

  const handleDelete = async (id) => {
    try {
      await deleteHistory(id);
      setRecords(records.filter((r) => r.id !== id));
    } catch (e) {
      alert(e.message);
    }
  };

  const formatTime = (ts) => {
    try {
      return new Date(ts).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    } catch { return ts; }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">历史记录</h2>
          <p className="text-sm text-gray-500 mt-1">查看所有 AI 生成记录</p>
        </div>
        <button className="btn-ghost text-sm" onClick={loadHistory}>🔄 刷新</button>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="card-flat p-4 flex gap-4">
              <div className="shimmer w-8 h-8" />
              <div className="shimmer h-4 flex-1" />
              <div className="shimmer w-20 h-4" />
            </div>
          ))}
        </div>
      ) : records.length === 0 ? (
        <div className="card p-12 text-center">
          <p className="text-4xl mb-3">📋</p>
          <p className="text-sm text-gray-400">暂无历史记录，开始使用 AI 功能吧！</p>
        </div>
      ) : (
        <div className="card divide-y divide-gray-50">
          {records.map((record) => {
            const typeInfo = TYPE_LABELS[record.type] || { label: record.type, icon: '📄', color: 'tag-gray' };
            const isExpanded = expanded === record.id;
            return (
              <div key={record.id}>
                <div
                  className="flex items-center gap-4 px-5 py-3.5 hover:bg-gray-50/60 transition-colors cursor-pointer"
                  onClick={() => setExpanded(isExpanded ? null : record.id)}
                >
                  <span className="text-lg">{typeInfo.icon}</span>
                  <span className={`tag ${typeInfo.color}`}>{typeInfo.label}</span>
                  <span className="flex-1 text-sm text-gray-700 truncate">{record.topic || record.title || '-'}</span>
                  <span className="text-xs text-gray-400 flex-shrink-0">{formatTime(record.created_at)}</span>
                  <button
                    className="text-gray-300 hover:text-red-500 transition-colors p-1"
                    onClick={(e) => { e.stopPropagation(); handleDelete(record.id); }}
                    title="删除"
                  >
                    ✕
                  </button>
                </div>
                {isExpanded && (
                  <div className="px-5 pb-4 animate-fade-in">
                    <pre className="text-xs text-gray-500 bg-gray-50 rounded-xl p-4 max-h-60 overflow-auto whitespace-pre-wrap">
                      {JSON.stringify(record.data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
