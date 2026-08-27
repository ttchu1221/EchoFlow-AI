const API_BASE = '/api';

// ── Token 自动刷新机制 ─────────────────────────────────
let _refreshPromise = null;

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) throw new Error('no_refresh_token');

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) throw new Error('refresh_failed');
  const data = await res.json();
  const newToken = data.data?.access_token;
  if (!newToken) throw new Error('refresh_failed');

  localStorage.setItem('token', newToken);
  return newToken;
}

function forceLogout() {
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.reload();
}

// ── 统一请求函数（自动携带 Token + 401 静默刷新）─────────
async function request(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // 如果 401 且有 refresh_token，尝试刷新
  if (res.status === 401 && localStorage.getItem('refresh_token')) {
    try {
      // 用锁防止并发多次刷新
      if (!_refreshPromise) {
        _refreshPromise = refreshAccessToken().finally(() => { _refreshPromise = null; });
      }
      const newToken = await _refreshPromise;

      // 用新 token 重试原请求
      const retryHeaders = { ...headers, Authorization: `Bearer ${newToken}` };
      const retryRes = await fetch(`${API_BASE}${path}`, { ...options, headers: retryHeaders });
      if (!retryRes.ok) {
        const err = await retryRes.json().catch(() => ({ detail: retryRes.statusText }));
        throw new Error(err.detail?.error || err.detail || '请求失败');
      }
      return retryRes.json();
    } catch (e) {
      // 刷新失败，强制登出
      forceLogout();
      throw e;
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail?.error || err.detail || '请求失败');
  }
  return res.json();
}

// ── 基础 ─────────────────────────────────────────────────
export async function getProviders() { return request('/providers'); }
export async function getPlatforms() { return request('/platforms'); }
export async function getHotSearch(platform, limit = 30) { return request(`/hot/${platform}?limit=${limit}`); }

// ── Phase 1: 标题 ────────────────────────────────────────
export async function generateTitles(data) { return request('/generate', { method: 'POST', body: JSON.stringify(data) }); }
export async function optimizeTitle(data) { return request('/optimize', { method: 'POST', body: JSON.stringify(data) }); }

// ── Phase 2: 趋势 / 评论 ────────────────────────────────
export async function analyzeTrends(data) { return request('/trends', { method: 'POST', body: JSON.stringify(data) }); }
export async function analyzeFeedback(data) { return request('/feedback', { method: 'POST', body: JSON.stringify(data) }); }

// ── Phase 3: 脚本 / 封面 / 发布 / 全流程 ────────────────
export async function generateScript(data) { return request('/script', { method: 'POST', body: JSON.stringify(data) }); }
export async function generateCover(data) { return request('/cover', { method: 'POST', body: JSON.stringify(data) }); }
export async function planPublish(data) { return request('/publish', { method: 'POST', body: JSON.stringify(data) }); }
export async function runFullPipeline(data) { return request('/pipeline', { method: 'POST', body: JSON.stringify(data) }); }

// ── Phase 4: 分析 / 记忆 ────────────────────────────────
export async function analyzePerformance(data) { return request('/analytics', { method: 'POST', body: JSON.stringify(data) }); }
export async function createProfile(data) { return request('/profiles', { method: 'POST', body: JSON.stringify(data) }); }
export async function listProfiles() { return request('/profiles'); }
export async function deleteProfile(id) { return request(`/profiles/${id}`, { method: 'DELETE' }); }

// ── 历史 ─────────────────────────────────────────────────
export async function getHistory(limit = 20, offset = 0, type = null) {
  let url = `/history?limit=${limit}&offset=${offset}`;
  if (type) url += `&type=${type}`;
  return request(url);
}
export async function deleteHistory(id) { return request(`/history/${id}`, { method: 'DELETE' }); }

// ── v1.1: 策略 / 增长闭环 ───────────────────────────────
export async function generateStrategy(data) { return request('/strategy', { method: 'POST', body: JSON.stringify(data) }); }
export async function runGrowthLoop(data) { return request('/growth-loop', { method: 'POST', body: JSON.stringify(data) }); }
export async function createGrowthMemory(data) { return request('/growth-memories', { method: 'POST', body: JSON.stringify(data) }); }
export async function getGrowthMemories(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(`/growth-memories${qs ? '?' + qs : ''}`);
}
export async function getGrowthStats(creatorId = null) {
  return request(`/growth-stats${creatorId ? '?creator_id=' + creatorId : ''}`);
}
export async function createStrategyMemory(data) { return request('/strategy-memories', { method: 'POST', body: JSON.stringify(data) }); }
export async function getStrategyMemories(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(`/strategy-memories${qs ? '?' + qs : ''}`);
}
export async function getActivePrompts(creatorId = null) {
  return request(`/active-prompts${creatorId ? '?creator_id=' + creatorId : ''}`);
}

// ── v1.4: 每日热点总结 ──────────────────────────────────
export async function generateDailyDigest(data = {}) { return request('/daily-digest/generate', { method: 'POST', body: JSON.stringify(data) }); }
export async function getTodayDigest() { return request('/daily-digest/today'); }
export async function getDigestByDate(date) { return request(`/daily-digest/${date}`); }
export async function listDigests(days = 30) { return request(`/daily-digest/list?days=${days}`); }
export async function getObsidianContent(date) { return fetch(`${API_BASE}/daily-digest/obsidian/${date}`).then(r => r.text()); }

// ── v3.0: 企业版 API ─────────────────────────────────────
export async function getEnterpriseDashboard() { return request('/v3/dashboard'); }
export async function cooDispatch(goal) { return request('/v3/coo/dispatch', { method: 'POST', body: JSON.stringify({ goal }) }); }
export async function getCooTasks(limit = 20) { return request(`/v3/coo/tasks?limit=${limit}`); }
export async function getCooTask(taskId) { return request(`/v3/coo/tasks/${taskId}`); }
export async function executeCooTask(taskId) { return request(`/v3/coo/tasks/${taskId}/execute`, { method: 'POST' }); }
export async function cooAnalyze(question) { return request('/v3/coo/analyze', { method: 'POST', body: JSON.stringify({ question }) }); }
export async function cooChat(message, onToken) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/v3/coo/chat`, {
    method: 'POST', headers, body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(`COO chat failed: ${res.status}`);

  // SSE 流式解析
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let fullContent = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try {
        const evt = JSON.parse(line.slice(6));
        if (evt.type === 'token' && evt.content) {
          fullContent += evt.content;
          onToken?.(fullContent, evt.content);
        }
      } catch { /* 忽略解析错误 */ }
    }
  }
  return { content: fullContent };
}
export async function getAgents() { return request('/v3/agents'); }
export async function getAgentDetail(agentId) { return request(`/v3/agents/${agentId}`); }
export async function executeAgentTask(agentId, action) { return request(`/v3/agents/${agentId}/execute`, { method: 'POST', body: JSON.stringify({ action }) }); }
export async function getKnowledge(category) { return request(`/v3/knowledge${category ? '?category=' + category : ''}`); }
export async function createKnowledge(item) { return request('/v3/knowledge', { method: 'POST', body: JSON.stringify(item) }); }
export async function getKnowledgeCategories() { return request('/v3/knowledge/categories'); }
export async function getGrowthBrain(creatorId) { return request(`/v3/growth-brain${creatorId ? '?creator_id=' + creatorId : ''}`); }
export async function getSystemStatus() { return request('/v3/system/status'); }

// ── 数据采集中心 API ─────────────────────────────────────
export async function getDataCollectionOverview(days = 7) { return request(`/data-collection/overview?days=${days}`); }
export async function getCollectionJobs(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(`/data-collection/jobs${qs ? '?' + qs : ''}`);
}
export async function createCollectionJob(data) {
  return request('/data-collection/jobs', { method: 'POST', body: JSON.stringify(data) });
}
export async function runCollectionJob(jobId) {
  return request(`/data-collection/jobs/${jobId}/run`, { method: 'POST' });
}
export async function manualCollect(data) {
  return request('/data-collection/collect', { method: 'POST', body: JSON.stringify(data) });
}
export async function askDataCollection(question) {
  return request('/data-collection/ask', { method: 'POST', body: JSON.stringify({ question }) });
}
export async function getCollectedContents(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(`/data-collection/contents${qs ? '?' + qs : ''}`);
}
export async function getDataQualityReport() { return request('/data-collection/quality'); }

// ── v3.0: 模型配置 API ───────────────────────────────────
export async function getLLMConfig() { return request('/v3/llm-config'); }
export async function updateLLMConfig(config) { return request('/v3/llm-config', { method: 'PUT', body: JSON.stringify(config) }); }
export async function getLLMProviders() { return request('/v3/llm-config/providers'); }
export async function testLLMConfig() { return request('/v3/llm-config/test', { method: 'POST' }); }

// ── 竞品监控 API ─────────────────────────────────────
export async function competitorAccounts(platform) { return request(`/competitor/accounts${platform ? '?platform=' + platform : ''}`); }
export async function competitorInsights(days = 7) { return request(`/competitor/insights?days=${days}`); }
export async function competitorAdd(body) { return request('/competitor/accounts', { method: 'POST', body: JSON.stringify(body) }); }
export async function competitorFetch(id, limit = 10) {
  return request('/competitor/fetch', { method: 'POST', body: JSON.stringify({ competitor_id: id, limit }) });
}
export async function competitorRemove(id) { return request(`/competitor/accounts/${id}`, { method: 'DELETE' }); }

// ── RAG 知识库 API ───────────────────────────────────────
export async function getRAGCollections() { return request('/rag/collections'); }
export async function getRAGDocuments(collection, page = 1, size = 20) {
  return request(`/rag/documents/${collection}?page=${page}&size=${size}`);
}
export async function uploadRAGDocument(file, collection) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('collection', collection);
  const token = localStorage.getItem('token');
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(`${API_BASE}/rag/upload`, { method: 'POST', headers, body: formData });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || '上传失败'); }
  return res.json();
}
export async function syncRAG(mode = 'all', platform = '', limit = 30) {
  return request('/rag/sync', { method: 'POST', body: JSON.stringify({ mode, platform, limit }) });
}
export async function searchRAG(question, collection, k = 5) {
  return request('/rag/search', { method: 'POST', body: JSON.stringify({ question, collection, k }) });
}
export async function queryRAG(question, collection = '') {
  return request('/rag/query', { method: 'POST', body: JSON.stringify({ question, collection }) });
}

// ── v3.0: AI 对话助手 API ────────────────────────────────
export async function getConversations(limit = 50) { return request(`/v3/chat/conversations?limit=${limit}`); }
export async function createConversation(data = {}) { return request('/v3/chat/conversations', { method: 'POST', body: JSON.stringify(data) }); }
export async function getConversation(convId) { return request(`/v3/chat/conversations/${convId}`); }
export async function deleteConversation(convId) { return request(`/v3/chat/conversations/${convId}`, { method: 'DELETE' }); }
export async function updateConversation(convId, data) { return request(`/v3/chat/conversations/${convId}`, { method: 'PUT', body: JSON.stringify(data) }); }

/**
 * 发送消息并以 SSE 流式接收回复
 * @param {string} convId - 对话 ID
 * @param {string} message - 消息内容
 * @param {function} onToken - 每收到一个 token 时的回调
 * @param {function} onDone - 流结束时的回调
 * @param {function} onError - 出错时的回调
 * @returns {function} abort - 调用可中断流式请求
 */
export function chatStream(convId, message, onToken, onDone, onError) {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/v3/chat/conversations/${convId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        onError?.(new Error(err.detail || '请求失败'));
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let doneEmitted = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;
          try {
            const data = JSON.parse(jsonStr);
            if (data.type === 'token') {
              onToken?.(data.content);
            } else if (data.type === 'done') {
              doneEmitted = true;
              onDone?.(data);
            }
          } catch (e) {
            // skip malformed JSON
          }
        }
      }

      if (!doneEmitted) {
        onDone?.({});
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        onError?.(e);
      }
    }
  })();

  return () => controller.abort();
}
