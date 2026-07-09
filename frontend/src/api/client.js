const API_BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || '请求失败');
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
export async function cooChat(message) { return request('/v3/coo/chat', { method: 'POST', body: JSON.stringify({ message }) }); }
export async function getAgents() { return request('/v3/agents'); }
export async function getAgentDetail(agentId) { return request(`/v3/agents/${agentId}`); }
export async function executeAgentTask(agentId, action) { return request(`/v3/agents/${agentId}/execute`, { method: 'POST', body: JSON.stringify({ action }) }); }
export async function getKnowledge(category) { return request(`/v3/knowledge${category ? '?category=' + category : ''}`); }
export async function createKnowledge(item) { return request('/v3/knowledge', { method: 'POST', body: JSON.stringify(item) }); }
export async function getKnowledgeCategories() { return request('/v3/knowledge/categories'); }
export async function getGrowthBrain(creatorId) { return request(`/v3/growth-brain${creatorId ? '?creator_id=' + creatorId : ''}`); }
export async function getSystemStatus() { return request('/v3/system/status'); }

// ── v3.0: 模型配置 API ───────────────────────────────────
export async function getLLMConfig() { return request('/v3/llm-config'); }
export async function updateLLMConfig(config) { return request('/v3/llm-config', { method: 'PUT', body: JSON.stringify(config) }); }
export async function getLLMProviders() { return request('/v3/llm-config/providers'); }
export async function testLLMConfig() { return request('/v3/llm-config/test', { method: 'POST' }); }

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
              onDone?.(data);
            }
          } catch (e) {
            // skip malformed JSON
          }
        }
      }

      onDone?.({});
    } catch (e) {
      if (e.name !== 'AbortError') {
        onError?.(e);
      }
    }
  })();

  return () => controller.abort();
}
