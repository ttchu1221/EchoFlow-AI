import { useState, useEffect } from 'react';

const API = '/api/schedules';

export default function SchedulePanel() {
  const [items, setItems] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: '', task_type: 'pipeline', trigger_type: 'cron',
    cron_expr: '0 9 * * 1-5', interval_seconds: 3600,
    params: { platform: 'douyin' }, enabled: true,
  });
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

  const create = async () => {
    try {
      const res = await fetch(API, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (data.code === 200) {
        setShowCreate(false);
        load();
      } else {
        alert(data.detail?.error || '创建失败');
      }
    } catch (e) { alert('请求失败'); }
  };

  const runNow = async (id) => {
    await fetch(`${API}/${id}/run`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    });
    alert('任务已触发');
  };

  const remove = async (id) => {
    if (!confirm('确认删除?')) return;
    await fetch(`${API}/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    });
    load();
  };

  const taskTypeLabels = {
    pipeline: '内容流水线', strategy: '策略分析',
    collect: '数据采集', custom: '自定义',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-txt-primary">⏰ 定时任务</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 bg-brand-500 text-white rounded-xl text-sm font-medium hover:bg-brand-600 transition-all"
        >
          + 新建任务
        </button>
      </div>

      {showCreate && (
        <div className="bg-panel-50/80 border border-panel-border rounded-xl p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-txt-secondary">任务名称</label>
              <input value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm" />
            </div>
            <div>
              <label className="text-sm text-txt-secondary">任务类型</label>
              <select value={form.task_type} onChange={e => setForm({...form, task_type: e.target.value})}
                className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm">
                {Object.entries(taskTypeLabels).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-txt-secondary">触发方式</label>
              <select value={form.trigger_type} onChange={e => setForm({...form, trigger_type: e.target.value})}
                className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm">
                <option value="cron">Cron 表达式</option>
                <option value="interval">固定间隔</option>
              </select>
            </div>
            {form.trigger_type === 'cron' ? (
              <div>
                <label className="text-sm text-txt-secondary">Cron 表达式</label>
                <input value={form.cron_expr} onChange={e => setForm({...form, cron_expr: e.target.value})}
                  placeholder="0 9 * * 1-5 (工作日 9 点)"
                  className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm" />
              </div>
            ) : (
              <div>
                <label className="text-sm text-txt-secondary">间隔（秒）</label>
                <input type="number" value={form.interval_seconds}
                  onChange={e => setForm({...form, interval_seconds: parseInt(e.target.value)})}
                  className="w-full mt-1 px-3 py-2 bg-panel-100 border border-panel-border rounded-lg text-txt-primary text-sm" />
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <button onClick={create} className="px-4 py-2 bg-brand-500 text-white rounded-lg text-sm">创建</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-panel-100 text-txt-muted rounded-lg text-sm">取消</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-txt-muted">加载中...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-txt-muted">暂无定时任务</div>
      ) : (
        <div className="space-y-3">
          {items.map(item => (
            <div key={item.id} className="bg-panel-50/80 border border-panel-border rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-txt-primary font-medium">{item.name}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${item.enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                      {item.enabled ? '启用' : '禁用'}
                    </span>
                    <span className="text-xs text-txt-muted bg-panel-100 px-2 py-0.5 rounded">
                      {taskTypeLabels[item.task_type] || item.task_type}
                    </span>
                  </div>
                  <div className="text-xs text-txt-muted mt-1">
                    {item.trigger_type === 'cron' ? `Cron: ${item.cron_expr}` : `间隔: ${item.interval_seconds}s`}
                    {item.last_run_at && ` | 上次执行: ${item.last_run_at?.slice(0, 16)}`}
                    {item.last_status && ` | 状态: ${item.last_status}`}
                    {` | 已执行 ${item.run_count || 0} 次`}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => runNow(item.id)} className="px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded-lg text-xs hover:bg-blue-500/30">▶ 立即执行</button>
                  <button onClick={() => remove(item.id)} className="px-3 py-1.5 bg-red-500/20 text-red-400 rounded-lg text-xs hover:bg-red-500/30">🗑</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
