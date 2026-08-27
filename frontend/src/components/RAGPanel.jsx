import { useState, useEffect, useRef, useCallback } from 'react';
import { getRAGCollections, getRAGDocuments, uploadRAGDocument, syncRAG, searchRAG } from '../api/client';

export default function RAGPanel() {
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState('');
  const [uploadResult, setUploadResult] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [docsTotal, setDocsTotal] = useState(0);
  const [docsPage, setDocsPage] = useState(1);
  const [docsLoading, setDocsLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadCollections();
  }, []);

  useEffect(() => {
    if (selectedCollection) {
      loadDocuments(1);
    }
  }, [selectedCollection]);

  const loadCollections = async () => {
    try {
      setLoading(true);
      const res = await getRAGCollections();
      setCollections(res.collections || []);
      if (res.collections?.length > 0 && !selectedCollection) {
        setSelectedCollection(res.collections[0].type);
      }
    } catch (e) {
      console.error('加载集合失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async (page = 1) => {
    if (!selectedCollection) return;
    try {
      setDocsLoading(true);
      const res = await getRAGDocuments(selectedCollection, page, 10);
      setDocuments(res.documents || []);
      setDocsTotal(res.total || 0);
      setDocsPage(page);
    } catch (e) {
      console.error('加载文档列表失败:', e);
    } finally {
      setDocsLoading(false);
    }
  };

  const doUpload = async (file) => {
    if (!file || !selectedCollection) return;
    if (!file.name.endsWith('.pdf')) {
      setUploadResult({ success: false, message: '仅支持 PDF 文件' });
      return;
    }
    try {
      setUploading(true);
      setUploadResult(null);
      const result = await uploadRAGDocument(file, selectedCollection);
      setUploadResult({ success: true, ...result });
      // 刷新文档列表
      loadDocuments(1);
    } catch (e) {
      setUploadResult({ success: false, message: e.message });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) doUpload(file);
  };

  // 拖拽处理
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) doUpload(file);
  }, [selectedCollection]);

  const handleSync = async (mode = 'all') => {
    try {
      setSyncing(true);
      setSyncResult(null);
      const result = await syncRAG(mode);
      setSyncResult(result);
      // 同步后刷新文档列表
      setTimeout(() => loadDocuments(1), 1000);
    } catch (e) {
      setSyncResult({ success: false, error: e.message });
    } finally {
      setSyncing(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() || !selectedCollection) return;
    try {
      setSearching(true);
      setSearchResults(null);
      const result = await searchRAG(searchQuery, selectedCollection, 5);
      setSearchResults(result);
    } catch (e) {
      setSearchResults({ success: false, error: e.message });
    } finally {
      setSearching(false);
    }
  };

  const collectionIcons = {
    platform_rules: '📋',
    viral_cases: '🔥',
    industry_knowledge: '📊',
    content_memories: '🧠',
  };

  if (loading) {
    return <div className="text-center py-12 text-txt-secondary">加载中...</div>;
  }

  const totalPages = Math.ceil(docsTotal / 10);

  return (
    <div className="space-y-6">
      {/* 集合概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {collections.map(col => (
          <button
            key={col.type}
            onClick={() => setSelectedCollection(col.type)}
            className={`p-4 rounded-xl border text-left transition-all ${
              selectedCollection === col.type
                ? 'bg-brand-500/15 border-brand-500/40 shadow-[0_0_10px_rgba(34,211,238,0.1)]'
                : 'bg-panel-100 border-panel-border hover:bg-panel-200'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{collectionIcons[col.type] || '📁'}</span>
              <span className="font-medium text-white text-sm">{col.name}</span>
            </div>
            <p className="text-xs text-txt-muted line-clamp-2">{col.description}</p>
          </button>
        ))}
      </div>

      {/* 上传区 + 同步区 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 拖拽上传区 */}
        <div className="bg-panel-100 rounded-xl border border-panel-border p-5">
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>📄</span> 上传文档
          </h3>
          <p className="text-xs text-txt-muted mb-4">
            拖拽或点击上传 PDF，文档将自动切分并向量化到「{collections.find(c => c.type === selectedCollection)?.name || ''}」。
          </p>

          {/* 拖拽区域 */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              dragActive
                ? 'border-brand-400 bg-brand-500/10 scale-[1.01]'
                : uploading
                  ? 'border-panel-border bg-panel-200 cursor-wait'
                  : 'border-panel-border hover:border-brand-500/50 hover:bg-panel-50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            {uploading ? (
              <div className="space-y-2">
                <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-sm text-brand-300">正在处理文档...</p>
              </div>
            ) : (
              <>
                <div className="text-4xl mb-3">{dragActive ? '📥' : '📎'}</div>
                <p className="text-sm text-txt-secondary">
                  {dragActive ? '松开即可上传' : '拖拽 PDF 到此处，或点击选择文件'}
                </p>
                <p className="text-xs text-txt-muted mt-1">支持 .pdf 格式</p>
              </>
            )}
          </div>

          {uploadResult && (
            <div className={`mt-3 p-3 rounded-lg text-sm ${
              uploadResult.success ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
            }`}>
              {uploadResult.success
                ? `✅ ${uploadResult.message}（${uploadResult.chunks} 个文档块）`
                : `❌ ${uploadResult.message}`}
            </div>
          )}
        </div>

        {/* 一键同步 */}
        <div className="bg-panel-100 rounded-xl border border-panel-border p-5">
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>🔄</span> 实时热点同步
          </h3>
          <p className="text-xs text-txt-muted mb-4">
            一键从 B站/抖音/小红书/微博 抓取实时热搜+热门内容，自动写入知识库。
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleSync('all')}
              disabled={syncing}
              className="px-4 py-2.5 rounded-xl text-sm font-medium bg-brand-500/20 text-brand-300 border border-brand-500/30 hover:bg-brand-500/30 disabled:opacity-50 transition-all"
            >
              {syncing ? (
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
                  同步中...
                </span>
              ) : '🚀 全量同步'}
            </button>
            <button
              onClick={() => handleSync('hot_search')}
              disabled={syncing}
              className="px-3 py-2 rounded-xl text-xs bg-panel-200 text-txt-secondary border border-panel-border hover:bg-panel-300 disabled:opacity-50 transition-all"
            >
              🔥 仅热搜
            </button>
            <button
              onClick={() => handleSync('popular')}
              disabled={syncing}
              className="px-3 py-2 rounded-xl text-xs bg-panel-200 text-txt-secondary border border-panel-border hover:bg-panel-300 disabled:opacity-50 transition-all"
            >
              📺 仅热门视频
            </button>
            <button
              onClick={() => handleSync('digest')}
              disabled={syncing}
              className="px-3 py-2 rounded-xl text-xs bg-panel-200 text-txt-secondary border border-panel-border hover:bg-panel-300 disabled:opacity-50 transition-all"
            >
              📰 今日 Digest
            </button>
          </div>
          {syncResult && (
            <div className={`mt-3 p-3 rounded-lg text-sm ${
              syncResult.success ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
            }`}>
              {syncResult.success
                ? `✅ 同步完成`
                : `❌ ${syncResult.error || '同步失败'}`}
            </div>
          )}
        </div>
      </div>

      {/* 已有文档列表 */}
      <div className="bg-panel-100 rounded-xl border border-panel-border p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-medium flex items-center gap-2">
            <span>📋</span> 已有文档
            <span className="text-xs text-txt-muted ml-2">
              {collections.find(c => c.type === selectedCollection)?.name} · 共 {docsTotal} 条
            </span>
          </h3>
          <button
            onClick={() => loadDocuments(docsPage)}
            className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
          >
            🔄 刷新
          </button>
        </div>

        {docsLoading ? (
          <div className="space-y-2">
            {[1,2,3].map(i => <div key={i} className="shimmer h-14 rounded-lg" />)}
          </div>
        ) : documents.length > 0 ? (
          <>
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {documents.map((doc, i) => (
                <div key={doc.id || i} className="p-3 rounded-lg bg-panel-50 border border-panel-border hover:border-brand-500/30 transition-all">
                  <p className="text-sm text-white line-clamp-2">{doc.content}</p>
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-xs text-txt-muted">{doc.full_length} 字</span>
                    {doc.source && <span className="text-xs text-txt-muted">来源: {doc.source}</span>}
                  </div>
                </div>
              ))}
            </div>
            {/* 分页 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4">
                <button
                  onClick={() => loadDocuments(docsPage - 1)}
                  disabled={docsPage <= 1}
                  className="px-3 py-1.5 rounded-lg text-xs bg-panel-200 text-txt-secondary disabled:opacity-30 hover:bg-panel-300 transition-all"
                >
                  上一页
                </button>
                <span className="text-xs text-txt-muted">{docsPage} / {totalPages}</span>
                <button
                  onClick={() => loadDocuments(docsPage + 1)}
                  disabled={docsPage >= totalPages}
                  className="px-3 py-1.5 rounded-lg text-xs bg-panel-200 text-txt-secondary disabled:opacity-30 hover:bg-panel-300 transition-all"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8">
            <span className="text-3xl block mb-2">📭</span>
            <p className="text-sm text-txt-muted">该集合暂无文档</p>
            <p className="text-xs text-txt-muted mt-1">上传 PDF 或同步热点数据后将在此展示</p>
          </div>
        )}
      </div>

      {/* 知识库检索测试 */}
      <div className="bg-panel-100 rounded-xl border border-panel-border p-5">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <span>🔍</span> 检索测试
        </h3>
        <div className="flex gap-3">
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="输入关键词测试检索效果..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-panel-50 border border-panel-border text-white text-sm placeholder-txt-muted focus:outline-none focus:border-brand-500/50"
          />
          <button
            onClick={handleSearch}
            disabled={searching || !searchQuery.trim()}
            className="px-4 py-2.5 rounded-xl text-sm font-medium bg-brand-500/20 text-brand-300 border border-brand-500/30 hover:bg-brand-500/30 disabled:opacity-50 transition-all"
          >
            {searching ? '检索中...' : '检索'}
          </button>
        </div>
        {searchResults && (
          <div className="mt-4 space-y-2">
            {searchResults.success && searchResults.results?.length > 0 ? (
              <>
                <p className="text-xs text-txt-muted">
                  在「{searchResults.collection_name}」中找到 {searchResults.total} 条结果：
                </p>
                {searchResults.results.map((item, i) => (
                  <div key={i} className="p-3 rounded-lg bg-panel-50 border border-panel-border">
                    <p className="text-sm text-white whitespace-pre-wrap line-clamp-3">{item.content}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-xs text-brand-400">相似度: {(1 / (1 + item.score)).toFixed(3)}</span>
                      {item.metadata?.platform && (
                        <span className="text-xs text-txt-muted">平台: {item.metadata.platform}</span>
                      )}
                      {item.metadata?.date && (
                        <span className="text-xs text-txt-muted">日期: {item.metadata.date}</span>
                      )}
                    </div>
                  </div>
                ))}
              </>
            ) : searchResults.success ? (
              <p className="text-sm text-txt-muted py-4 text-center">暂无匹配结果，请先上传文档或同步数据</p>
            ) : (
              <p className="text-sm text-red-400">❌ {searchResults.error || '检索失败'}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
