import { useState, useEffect } from 'react';
import { competitorAccounts, competitorInsights, competitorAdd, competitorFetch, competitorRemove } from '../api/client';

export default function CompetitorPanel() {
  const [accounts, setAccounts] = useState([]);
  const [insights, setInsights] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', platform: 'douyin', account_id: '', tags: [] });
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [accData, insData] = await Promise.all([
        competitorAccounts(),
        competitorInsights(7),
      ]);
      setAccounts(accData.data || []);
      setInsights(insData.data?.insights || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const addAccount = async () => {
    try {
      const data = await competitorAdd(form);
      if (data.code === 200) {
        setShowAdd(false);
        setForm({ name: '', platform: 'douyin', account_id: '', tags: [] });
        load();
      } else {
        alert(data.detail?.error || '添加失败');
      }
    } catch (e) { alert(e.message || '请求失败'); }
  };

  const fetchContent = async (id) => {
    try {
      const data = await competitorFetch(id);
      if (data.code === 200) {
        alert(`采集完成: 获取 ${data.data.fetched || 0} 条，新增 ${data.data.saved || data.data.new || 0} 条`);
        load();
      }
    } catch (e) { alert(e.message || '采集失败'); }
  };

  const remove = async (id) => {
    if (!confirm('确认删除?')) return;
    await competitorRemove(id);
    load();
  };

  const platformIcons = {
    douyin: '🎵', xiaohongshu: '📕', bilibili: '📺', kuaishou: '⚡',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-txt-primary">👁 竞品监控</h2>
        <button onClick={() => setShowAdd(!showAdd)}
          className="px-4 py-2 bg-brand-500 text-white rounded-xl text-sm font-medium hover:bg-brand-600 transition-all">
          + 添加竞品
        </button>
      </div>

      {showAdd && (
        <div className="bg-panel-50/80 border border-panel-border rounded-xl p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-txt-secondary">竞品名称</label>
              <input value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm" />
            </div>
            <div>
              <label className="text-sm text-txt-secondary">平台</label>
              <select value={form.platform} onChange={e => setForm({...form, platform: e.target.value})}
                className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm">
                <option value="douyin">🎵 抖音</option>
                <option value="xiaohongshu">📕 小红书</option>
                <option value="bilibili">📺 B站</option>
                <option value="kuaishou">⚡ 快手</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="text-sm text-txt-secondary">账号 ID 或主页 URL</label>
              <input value={form.account_id} onChange={e => setForm({...form, account_id: e.target.value})}
                className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={addAccount} className="px-4 py-2 bg-brand-500 text-white rounded-lg text-sm">添加</button>
            <button onClick={() => setShowAdd(false)} className="px-4 py-2 bg-panel-100 text-txt-muted rounded-lg text-sm">取消</button>
          </div>
        </div>
      )}

      {/* 竞品列表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {accounts.map(acc => (
          <div key={acc.id} className="bg-panel-50/80 border border-panel-border rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">{platformIcons[acc.platform] || '📊'}</span>
                <div>
                  <div className="text-txt-primary font-medium">{acc.name}</div>
                  <div className="text-xs text-txt-muted">{acc.platform} | {acc.account_id}</div>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => fetchContent(acc.id)}
                  className="px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded-lg text-xs hover:bg-blue-500/30">
                  🔄 采集
                </button>
                <button onClick={() => remove(acc.id)}
                  className="px-3 py-1.5 bg-red-500/20 text-red-400 rounded-lg text-xs hover:bg-red-500/30">
                  🗑
                </button>
              </div>
            </div>
            <div className="text-xs text-txt-muted mt-2">
              内容: {acc.content_count || 0} 条
              {acc.last_checked_at && ` | 上次采集: ${acc.last_checked_at?.slice(0, 16)}`}
            </div>
          </div>
        ))}
      </div>

      {/* 洞察分析 */}
      {insights.length > 0 && (
        <div className="bg-panel-50/80 border border-panel-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-txt-secondary mb-4">📊 近 7 天竞品洞察</h3>
          <div className="space-y-3">
            {insights.map((ins, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="w-8 text-center text-lg">{platformIcons[ins.platform] || '📊'}</div>
                <div className="flex-1">
                  <div className="text-sm text-txt-primary">{ins.competitor_name}</div>
                  <div className="text-xs text-txt-muted">{ins.total_content} 条内容</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-brand-400">平均 {ins.avg_views?.toLocaleString()} 浏览</div>
                  <div className="text-xs text-txt-muted">平均 {ins.avg_likes?.toLocaleString()} 点赞</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {accounts.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="text-4xl mb-3">👁</div>
          <div className="text-txt-muted">暂无竞品监控</div>
          <div className="text-xs text-txt-muted mt-1">添加竞品账号，自动采集和分析竞品内容</div>
        </div>
      )}
    </div>
  );
}
