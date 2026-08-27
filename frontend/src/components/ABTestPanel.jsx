import { useState, useEffect } from 'react';

const API = '/api/abtest';

export default function ABTestPanel() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(API, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const data = await res.json();
      if (data.code === 200) setItems(data.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const statusColors = {
    created: 'bg-gray-500/20 text-gray-400',
    running: 'bg-blue-500/20 text-blue-400',
    completed: 'bg-green-500/20 text-green-400',
  };

  const statusLabels = { created: '已创建', running: '进行中', completed: '已完成' };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-txt-primary">🧪 A/B 测试</h2>
        <button className="px-4 py-2 bg-brand-500 text-white rounded-xl text-sm font-medium hover:bg-brand-600 transition-all">
          + 新建测试
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-txt-muted">加载中...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-4xl mb-3">🧪</div>
          <div className="text-txt-muted">暂无 A/B 测试</div>
          <div className="text-xs text-txt-muted mt-1">创建测试来对比不同内容方案的效果</div>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(item => (
            <div key={item.id} className="bg-panel-50/80 border border-panel-border rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-txt-primary font-medium">{item.name}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${statusColors[item.status]}`}>
                      {statusLabels[item.status]}
                    </span>
                  </div>
                  <div className="text-xs text-txt-muted mt-1">
                    {item.variants?.length || 0} 个变体 | 指标: {item.metric}
                    {item.winner_variant_id && ` | 优胜: ${item.winner_variant_id}`}
                    {` | 创建: ${item.created_at?.slice(0, 10)}`}
                  </div>
                </div>
                <div className="flex gap-2">
                  {item.status === 'created' && (
                    <button className="px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded-lg text-xs hover:bg-blue-500/30">
                      ▶ 启动
                    </button>
                  )}
                  {item.status === 'running' && (
                    <button className="px-3 py-1.5 bg-green-500/20 text-green-400 rounded-lg text-xs hover:bg-green-500/30">
                      🏁 结束
                    </button>
                  )}
                </div>
              </div>

              {/* 变体列表 */}
              <div className="mt-3 grid grid-cols-2 lg:grid-cols-3 gap-2">
                {item.variants?.map(v => {
                  const result = item.results?.find(r => r.variant_id === v.variant_id);
                  return (
                    <div key={v.variant_id} className="bg-panel-100 rounded-lg p-3">
                      <div className="text-sm text-txt-primary font-medium">{v.name}</div>
                      <div className="text-xs text-txt-muted mt-1">{v.platform}</div>
                      {result && (
                        <div className="mt-2 space-y-1">
                          <div className="text-xs text-txt-muted">浏览: {result.views}</div>
                          <div className="text-xs text-txt-muted">点赞: {result.likes}</div>
                          <div className="text-xs text-brand-400">互动率: {(result.engagement_rate * 100).toFixed(1)}%</div>
                        </div>
                      )}
                      {item.winner_variant_id === v.variant_id && (
                        <div className="mt-2 text-xs text-green-400 font-medium">🏆 优胜</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
