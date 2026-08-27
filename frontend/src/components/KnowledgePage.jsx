import { useState, useEffect } from 'react';
import { getKnowledge, getKnowledgeCategories, createKnowledge } from '../api/client';
import RAGPanel from './RAGPanel';

const TABS = [
  { id: 'knowledge', label: '知识条目', icon: '📚' },
  { id: 'rag', label: '知识库管理', icon: '🧠' },
];

export default function KnowledgePage() {
  const [activeTab, setActiveTab] = useState('knowledge');
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newItem, setNewItem] = useState({ title: '', content: '', category: 'market', importance: 'medium' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [knowledgeRes, catRes] = await Promise.all([
        getKnowledge(),
        getKnowledgeCategories(),
      ]);
      setItems(knowledgeRes.items || []);
      setCategories(catRes.categories || []);
    } catch (e) {
      console.error('加载知识库失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = async (catId) => {
    setActiveCategory(catId === activeCategory ? null : catId);
    try {
      setLoading(true);
      const result = await getKnowledge(catId === activeCategory ? null : catId);
      setItems(result.items || []);
    } catch (e) {
      console.error('筛选失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newItem.title.trim() || !newItem.content.trim()) return;
    try {
      await createKnowledge(newItem);
      setNewItem({ title: '', content: '', category: 'market', importance: 'medium' });
      setShowCreate(false);
      loadData();
    } catch (e) {
      console.error('创建失败:', e);
    }
  };

  const importanceColors = {
    high: 'tag-red',
    medium: 'tag-amber',
    low: 'tag-green',
  };

  const categoryIcons = {
    market: '🌐', product: '📦', content: '✍️',
    creator: '👤', ads: '📊', case: '💡',
  };

  return (
    <div className="dashboard-container min-h-screen p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white dashboard-glow-text">知识中心</h1>
          <p className="text-txt-secondary mt-1">企业知识库 · RAG 向量检索 · 持续学习</p>
        </div>
        {activeTab === 'knowledge' && (
          <button onClick={() => setShowCreate(!showCreate)} className="btn-primary">
            {showCreate ? '取消' : '+ 新建知识'}
          </button>
        )}
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-2 mb-6">
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
      {activeTab === 'rag' ? (
        <RAGPanel />
      ) : (
        <>

      {/* 新建知识表单 */}
      {showCreate && (
        <div className="dashboard-panel rounded-2xl p-6 mb-6">
          <h3 className="text-lg font-bold text-white mb-4">📝 新建知识条目</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <input
              type="text"
              className="input"
              placeholder="标题"
              value={newItem.title}
              onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
            />
            <div className="flex gap-3">
              <select
                className="select flex-1"
                value={newItem.category}
                onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
              >
                {categories.map(c => (
                  <option key={c.id} value={c.id}>{c.icon} {c.name}</option>
                ))}
              </select>
              <select
                className="select flex-1"
                value={newItem.importance}
                onChange={(e) => setNewItem({ ...newItem, importance: e.target.value })}
              >
                <option value="high">🔴 高</option>
                <option value="medium">🟡 中</option>
                <option value="low">🟢 低</option>
              </select>
            </div>
          </div>
          <textarea
            className="textarea h-24 mb-4"
            placeholder="知识内容..."
            value={newItem.content}
            onChange={(e) => setNewItem({ ...newItem, content: e.target.value })}
          />
          <button onClick={handleCreate} className="btn-primary">保存</button>
        </div>
      )}

      {/* 分类筛选 */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => { setActiveCategory(null); loadData(); }}
          className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
            !activeCategory
              ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
              : 'bg-panel-100 text-txt-secondary border border-panel-border hover:bg-panel-200'
          }`}
        >
          全部
        </button>
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => handleFilter(cat.id)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              activeCategory === cat.id
                ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                : 'bg-panel-100 text-txt-secondary border border-panel-border hover:bg-panel-200'
            }`}
          >
            {cat.icon} {cat.name}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3,4,5,6].map(i => <div key={i} className="shimmer h-40 rounded-xl" />)}
        </div>
      ) : items.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => (
            <div key={item.id} className="dashboard-panel rounded-2xl p-5 hover:scale-[1.01] transition-all">
              <div className="flex items-start justify-between mb-3">
                <span className="text-2xl">{categoryIcons[item.category] || '📄'}</span>
                <span className={importanceColors[item.importance] || 'tag-gray'}>
                  {item.importance === 'high' ? '高' : item.importance === 'medium' ? '中' : '低'}
                </span>
              </div>
              <h4 className="text-base font-bold text-white mb-2">{item.title}</h4>
              <p className="text-sm text-txt-secondary line-clamp-3">{item.content}</p>
              {item.created_at && (
                <p className="text-xs text-txt-muted mt-3">{new Date(item.created_at).toLocaleDateString()}</p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="dashboard-panel rounded-2xl p-12 text-center">
          <span className="text-5xl mb-4 block">📚</span>
          <p className="text-lg font-medium text-txt-secondary">暂无知识条目</p>
          <p className="text-sm text-txt-muted mt-1">点击右上角「新建知识」添加</p>
        </div>
      )}
        </>
      )}
    </div>
  );
}
