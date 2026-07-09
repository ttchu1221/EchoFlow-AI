import { useState, useEffect } from 'react';
import { getSystemStatus, getLLMConfig, updateLLMConfig, getLLMProviders, testLLMConfig } from '../api/client';
import CostDashboard from './CostDashboard';
import AccountsPanel from './AccountsPanel';
import PlatformSyncPanel from './PlatformSyncPanel';
import TeamPanel from './TeamPanel';

const TABS = [
  { id: 'overview', label: '系统概览', icon: '🖥️' },
  { id: 'model', label: '模型配置', icon: '🤖' },
  { id: 'cost', label: '成本控制', icon: '💰' },
  { id: 'accounts', label: '账号管理', icon: '🔗' },
  { id: 'sync', label: '平台同步', icon: '🔌' },
  { id: 'team', label: '团队管理', icon: '👥' },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const result = await getSystemStatus();
      setStatus(result);
    } catch (e) {
      console.error('加载系统状态失败:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white dashboard-glow-text">系统设置</h1>
        <p className="text-txt-secondary mt-1">系统状态 · 成本管理 · 团队配置</p>
      </div>

      {/* Tab 切换 */}
      <div className="flex flex-wrap gap-2 mb-6">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                : 'bg-panel-100 text-txt-secondary border border-panel-border hover:bg-panel-200'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 内容 */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* 系统信息 */}
          <div className="dashboard-panel rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">📋 系统信息</h3>
            {loading ? (
              <div className="shimmer h-32 rounded-xl" />
            ) : status ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-panel-100/50">
                  <p className="text-xs text-txt-muted">版本</p>
                  <p className="text-lg font-bold text-white mt-1">{status.version}</p>
                </div>
                <div className="p-4 rounded-xl bg-panel-100/50">
                  <p className="text-xs text-txt-muted">版本类型</p>
                  <p className="text-lg font-bold text-brand-400 mt-1">{status.edition}</p>
                </div>
                <div className="p-4 rounded-xl bg-panel-100/50">
                  <p className="text-xs text-txt-muted">MongoDB</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`w-2 h-2 rounded-full ${status.services.mongodb === 'connected' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                    <p className="text-sm font-medium text-white">{status.services.mongodb}</p>
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-panel-100/50">
                  <p className="text-xs text-txt-muted">Redis</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`w-2 h-2 rounded-full ${status.services.redis === 'connected' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                    <p className="text-sm font-medium text-white">{status.services.redis}</p>
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          {/* Agent 状态 */}
          {status?.agents && (
            <div className="dashboard-panel rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">🤖 Agent 状态</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(status.agents).map(([id, agent]) => (
                  <div key={id} className="p-3 rounded-xl bg-panel-100/50 flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${agent.status === 'active' ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                    <span className="text-sm text-white">{id}</span>
                    <span className="text-xs text-txt-muted ml-auto">{agent.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 技术栈 */}
          <div className="dashboard-panel rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">🛠️ 技术栈</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { name: 'React 18', icon: '⚛️' },
                { name: 'FastAPI', icon: '🚀' },
                { name: 'MongoDB', icon: '🍃' },
                { name: 'Redis', icon: '🔴' },
                { name: 'Tailwind CSS', icon: '🎨' },
                { name: 'ECharts', icon: '📊' },
                { name: 'Three.js', icon: '🌐' },
                { name: 'PyJWT', icon: '🔐' },
              ].map(tech => (
                <div key={tech.name} className="p-3 rounded-xl bg-panel-100/50 text-center">
                  <span className="text-2xl">{tech.icon}</span>
                  <p className="text-xs text-txt-secondary mt-1">{tech.name}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'model' && <ModelConfigPanel />}
      {activeTab === 'cost' && <CostDashboard />}
      {activeTab === 'accounts' && <AccountsPanel />}
      {activeTab === 'sync' && <PlatformSyncPanel />}
      {activeTab === 'team' && <TeamPanel />}
    </div>
  );
}

function ModelConfigPanel() {
  const [config, setConfig] = useState({ provider: 'mimo', base_url: '', model: '', api_key_masked: '', has_key: false, temperature: 0.7, max_tokens: 4096 });
  const [providers, setProviders] = useState([]);
  const [editKey, setEditKey] = useState('');
  const [editBaseUrl, setEditBaseUrl] = useState('');
  const [editModel, setEditModel] = useState('');
  const [editProvider, setEditProvider] = useState('mimo');
  const [editTemp, setEditTemp] = useState(0.7);
  const [editMaxTokens, setEditMaxTokens] = useState(4096);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [cfg, prov] = await Promise.all([getLLMConfig(), getLLMProviders()]);
      setConfig(cfg);
      setProviders(prov.providers || []);
      setEditProvider(cfg.provider || 'mimo');
      setEditBaseUrl(cfg.base_url || '');
      setEditModel(cfg.model || '');
      setEditTemp(cfg.temperature ?? 0.7);
      setEditMaxTokens(cfg.max_tokens ?? 4096);
    } catch (e) {
      console.error('加载模型配置失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = (pid) => {
    setEditProvider(pid);
    const prov = providers.find(p => p.id === pid);
    if (prov) {
      setEditBaseUrl(prov.default_base_url);
      setEditModel(prov.default_model);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMsg('');
      const payload = { provider: editProvider, base_url: editBaseUrl, model: editModel, temperature: editTemp, max_tokens: editMaxTokens };
      if (editKey) payload.api_key = editKey;
      const result = await updateLLMConfig(payload);
      setMsg('✅ 配置已保存并立即生效');
      setEditKey('');
      setConfig(result.config || config);
      setTestResult(null);
    } catch (e) {
      setMsg('❌ 保存失败: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      const result = await testLLMConfig();
      setTestResult(result);
    } catch (e) {
      setTestResult({ success: false, message: e.message });
    } finally {
      setTesting(false);
    }
  };

  if (loading) return <div className="dashboard-panel rounded-2xl p-6"><div className="shimmer h-48 rounded-xl" /></div>;

  return (
    <div className="space-y-6">
      <div className="dashboard-panel rounded-2xl p-6">
        <h3 className="text-lg font-bold text-white mb-6">🤖 模型配置</h3>
        <p className="text-sm text-txt-secondary mb-6">配置 LLM 提供商、API Key 和模型参数。修改后立即生效，无需重启。</p>

        {/* 提供商选择 */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-txt-secondary mb-2">模型提供商</label>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {providers.map(p => (
              <button
                key={p.id}
                onClick={() => handleProviderChange(p.id)}
                className={`p-3 rounded-xl text-sm font-medium transition-all border ${
                  editProvider === p.id
                    ? 'bg-brand-500/20 text-brand-300 border-brand-500/40 shadow-[0_0_10px_rgba(34,211,238,0.15)]'
                    : 'bg-panel-100 text-txt-secondary border-panel-border hover:bg-panel-200'
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        {/* 表单字段 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">API Base URL</label>
            <input
              value={editBaseUrl}
              onChange={e => setEditBaseUrl(e.target.value)}
              placeholder="https://api.example.com/v1"
              className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-white text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">模型名称</label>
            <input
              value={editModel}
              onChange={e => setEditModel(e.target.value)}
              placeholder="model-name"
              className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-white text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">
              API Key {config.has_key && <span className="text-brand-400 text-xs ml-1">(当前: {config.api_key_masked})</span>}
            </label>
            <input
              type="password"
              value={editKey}
              onChange={e => setEditKey(e.target.value)}
              placeholder={config.has_key ? '留空则保持现有 Key 不变' : '请输入 API Key'}
              className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-white text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">Temperature ({editTemp})</label>
            <input
              type="range" min="0" max="2" step="0.1"
              value={editTemp}
              onChange={e => setEditTemp(parseFloat(e.target.value))}
              className="w-full mt-2 accent-brand-500"
            />
            <div className="flex justify-between text-xs text-txt-muted mt-1">
              <span>精确 (0)</span><span>平衡 (1)</span><span>创意 (2)</span>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-txt-secondary mb-1.5">Max Tokens</label>
            <input
              type="number" min="100" max="128000" step="100"
              value={editMaxTokens}
              onChange={e => setEditMaxTokens(parseInt(e.target.value) || 4096)}
              className="w-full px-4 py-2.5 bg-panel-100 border border-panel-border rounded-xl text-white text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>
        </div>

        {/* 按钮 */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2.5 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
          >
            {saving ? '保存中...' : '💾 保存配置'}
          </button>
          <button
            onClick={handleTest}
            disabled={testing || !config.has_key}
            className="px-6 py-2.5 bg-panel-100 hover:bg-panel-200 text-txt-secondary border border-panel-border rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
          >
            {testing ? '测试中...' : '🔌 测试连接'}
          </button>
          {msg && <span className="text-sm">{msg}</span>}
        </div>

        {/* 测试结果 */}
        {testResult && (
          <div className={`mt-4 p-4 rounded-xl text-sm ${testResult.success ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300' : 'bg-red-500/10 border border-red-500/30 text-red-300'}`}>
            {testResult.success ? `✅ ${testResult.message}` : `❌ ${testResult.message}`}
            {testResult.response && <p className="mt-1 text-xs opacity-70">模型回复: {testResult.response}</p>}
          </div>
        )}
      </div>

      {/* 当前配置摘要 */}
      <div className="dashboard-panel rounded-2xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">📋 当前生效配置</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { label: '提供商', value: config.provider },
            { label: '模型', value: config.model },
            { label: 'Base URL', value: config.base_url },
            { label: 'API Key', value: config.has_key ? config.api_key_masked : '未配置' },
            { label: 'Temperature', value: config.temperature },
            { label: 'Max Tokens', value: config.max_tokens },
          ].map(item => (
            <div key={item.label} className="p-3 rounded-xl bg-panel-100/50">
              <p className="text-xs text-txt-muted">{item.label}</p>
              <p className="text-sm font-medium text-white mt-1 truncate">{item.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
