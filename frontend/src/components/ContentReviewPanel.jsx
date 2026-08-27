import { useState, useEffect } from 'react';

const API = '/api/content';

export default function ContentReviewPanel() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [reviewComment, setReviewComment] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: 1, page_size: 50 });
      if (statusFilter) params.set('status', statusFilter);
      const res = await fetch(`${API}?${params}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const data = await res.json();
      if (data.code === 200) {
        setItems(data.data.items || []);
        setTotal(data.data.total || 0);
      }
    } catch (e) {
      console.error('加载失败:', e);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, [statusFilter]);

  const doReview = async (id, action) => {
    try {
      const res = await fetch(`${API}/${id}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ action, comment: reviewComment }),
      });
      const data = await res.json();
      if (data.code === 200) {
        setReviewComment('');
        setSelected(null);
        load();
      } else {
        alert(data.detail?.error || '操作失败');
      }
    } catch (e) {
      alert('请求失败: ' + e.message);
    }
  };

  const statusColors = {
    draft: 'bg-gray-500/20 text-gray-400',
    pending_review: 'bg-yellow-500/20 text-yellow-400',
    approved: 'bg-green-500/20 text-green-400',
    rejected: 'bg-red-500/20 text-red-400',
    publishing: 'bg-blue-500/20 text-blue-400',
    published: 'bg-emerald-500/20 text-emerald-400',
    failed: 'bg-red-500/20 text-red-400',
  };

  const statusLabels = {
    draft: '草稿', pending_review: '待审核', approved: '已通过',
    rejected: '已驳回', publishing: '发布中', published: '已发布', failed: '发布失败',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-txt-primary">📋 内容审核</h2>
        <div className="flex gap-2">
          {['', 'draft', 'pending_review', 'approved', 'published'].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === s
                  ? 'bg-brand-500 text-white'
                  : 'bg-panel-100 text-txt-muted hover:text-txt-primary'
              }`}
            >
              {s ? statusLabels[s] || s : '全部'}
            </button>
          ))}
        </div>
      </div>

      <div className="text-sm text-txt-muted">共 {total} 条内容</div>

      {loading ? (
        <div className="text-center py-12 text-txt-muted">加载中...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-txt-muted">暂无内容</div>
      ) : (
        <div className="space-y-3">
          {items.map(item => (
            <div
              key={item.id}
              className="bg-panel-50/80 border border-panel-border rounded-xl p-4 hover:border-brand-500/30 transition-colors cursor-pointer"
              onClick={() => setSelected(selected === item.id ? null : item.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-txt-primary font-medium">{item.title}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${statusColors[item.status]}`}>
                      {statusLabels[item.status]}
                    </span>
                    <span className="text-xs text-txt-muted bg-panel-100 px-2 py-0.5 rounded">
                      {item.platform}
                    </span>
                  </div>
                  <div className="text-xs text-txt-muted mt-1">
                    作者: {item.author_name} | 更新: {item.updated_at?.slice(0, 16)}
                    {item.reviewer_name && ` | 审核: ${item.reviewer_name}`}
                  </div>
                </div>
              </div>

              {selected === item.id && (
                <div className="mt-4 pt-4 border-t border-panel-border space-y-3">
                  {item.review_comment && (
                    <div className="text-sm text-txt-secondary bg-panel-100 rounded-lg p-3">
                      <span className="text-txt-muted">审核意见:</span> {item.review_comment}
                    </div>
                  )}

                  {item.status === 'pending_review' && (
                    <>
                      <textarea
                        value={reviewComment}
                        onChange={(e) => setReviewComment(e.target.value)}
                        placeholder="审核意见（可选）"
                        className="w-full px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-sm text-txt-primary placeholder-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                        rows={2}
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={(e) => { e.stopPropagation(); doReview(item.id, 'approve'); }}
                          className="px-4 py-2 bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded-lg text-sm font-medium transition-all"
                        >
                          ✅ 通过
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); doReview(item.id, 'reject'); }}
                          className="px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg text-sm font-medium transition-all"
                        >
                          ❌ 驳回
                        </button>
                      </div>
                    </>
                  )}

                  {item.status === 'approved' && (
                    <button
                      onClick={(e) => { e.stopPropagation(); doReview(item.id, 'publish'); }}
                      className="px-4 py-2 bg-brand-500 text-white rounded-lg text-sm font-medium hover:bg-brand-600 transition-all"
                    >
                      🚀 发布
                    </button>
                  )}

                  {(item.status === 'draft' || item.status === 'rejected') && (
                    <button
                      onClick={(e) => { e.stopPropagation(); doReview(item.id, 'submit'); }}
                      className="px-4 py-2 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded-lg text-sm font-medium transition-all"
                    >
                      📤 提交审核
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
