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
