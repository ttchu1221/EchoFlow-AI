import { useState, useEffect } from 'react';

const API_AUTH = '/api/auth';
const API_TEAM = '/api/team';

export default function TeamPanel() {
  const [users, setUsers] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState('users');

  const load = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const [usersRes, actRes] = await Promise.all([
        fetch(`${API_AUTH}/users`, { headers }),
        fetch(`${API_TEAM}/activity?limit=50`, { headers }),
      ]);
      const usersData = await usersRes.json();
      const actData = await actRes.json();
      if (usersData.code === 200) setUsers(usersData.data || []);
      if (actData.code === 200) setActivity(actData.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const updateRole = async (userId, role) => {
    await fetch(`${API_AUTH}/users/${userId}/role?role=${role}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    });
    load();
  };

  const toggleStatus = async (userId, active) => {
    await fetch(`${API_AUTH}/users/${userId}/status?active=${active}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    });
    load();
  };

  const roleColors = {
    admin: 'bg-red-500/20 text-red-400',
    editor: 'bg-blue-500/20 text-blue-400',
    reviewer: 'bg-green-500/20 text-green-400',
    viewer: 'bg-gray-500/20 text-gray-400',
  };

  const roleLabels = { admin: '管理员', editor: '编辑', reviewer: '审核员', viewer: '只读' };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-txt-primary">👥 团队管理</h2>
        <div className="flex gap-2">
          <button onClick={() => setTab('users')}
            className={`px-3 py-1.5 rounded-lg text-sm ${tab === 'users' ? 'bg-brand-500 text-white' : 'bg-panel-100 text-txt-muted'}`}>
            成员
          </button>
          <button onClick={() => setTab('activity')}
            className={`px-3 py-1.5 rounded-lg text-sm ${tab === 'activity' ? 'bg-brand-500 text-white' : 'bg-panel-100 text-txt-muted'}`}>
            操作日志
          </button>
        </div>
      </div>

      {tab === 'users' && (
        <div className="space-y-3">
          {users.map(user => (
            <div key={user.id} className="bg-panel-50/80 border border-panel-border rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400 font-bold">
                    {user.display_name?.[0] || user.username[0]}
                  </div>
                  <div>
                    <div className="text-txt-primary font-medium">{user.display_name}</div>
                    <div className="text-xs text-txt-muted">@{user.username}</div>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs ${roleColors[user.role]}`}>
                    {roleLabels[user.role]}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={user.role}
                    onChange={e => updateRole(user.id, e.target.value)}
                    className="px-2 py-1 bg-panel-100 border border-panel-border rounded text-xs text-txt-primary"
                  >
                    {Object.entries(roleLabels).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => toggleStatus(user.id, !user.last_login)}
                    className="px-3 py-1.5 bg-panel-100 text-txt-muted rounded-lg text-xs hover:bg-panel-200"
                  >
                    {user.last_login ? '禁用' : '启用'}
                  </button>
                </div>
              </div>
              <div className="text-xs text-txt-muted mt-2">
                注册: {user.created_at?.slice(0, 10)}
                {user.last_login && ` | 最后登录: ${user.last_login?.slice(0, 16)}`}
              </div>
            </div>
          ))}
          {users.length === 0 && !loading && (
            <div className="text-center py-12 text-txt-muted">暂无成员</div>
          )}
        </div>
      )}

      {tab === 'activity' && (
        <div className="space-y-2">
          {activity.map((act, i) => (
            <div key={act.id || i} className="bg-panel-50/80 border border-panel-border rounded-xl px-4 py-3 flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-panel-100 flex items-center justify-center text-sm">
                {act.action === 'comment' ? '💬' : act.action === 'review' ? '📋' : act.action === 'publish' ? '🚀' : '📝'}
              </div>
              <div className="flex-1">
                <div className="text-sm text-txt-primary">
                  <span className="font-medium">{act.username}</span>
                  <span className="text-txt-muted"> {act.action} </span>
                  <span className="text-txt-secondary">{act.target_name || act.target_id}</span>
                </div>
                <div className="text-xs text-txt-muted">{act.timestamp?.replace('T', ' ').slice(0, 19)}</div>
              </div>
            </div>
          ))}
          {activity.length === 0 && !loading && (
            <div className="text-center py-12 text-txt-muted">暂无操作记录</div>
          )}
        </div>
      )}
    </div>
  );
}
