/**
 * LLM 提供商全局状态管理
 * 使用 localStorage 持久化用户选择，所有面板共享同一选择。
 */

const STORAGE_KEY = 'echoflow_llm_provider';

/** 获取当前选中的 LLM 提供商 ID（null 表示使用后端默认值） */
export function getLLMProvider() {
  return localStorage.getItem(STORAGE_KEY) || null;
}

/** 设置 LLM 提供商（传 null 则清除选择，使用后端默认值） */
export function setLLMProvider(provider) {
  if (provider) {
    localStorage.setItem(STORAGE_KEY, provider);
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
}

/**
 * 将 llm_provider 字段注入到请求数据中。
 * 如果用户已选择提供商，自动附加；否则不附加（后端使用默认值）。
 */
export function withLLMProvider(data) {
  const provider = getLLMProvider();
  if (provider) {
    return { ...data, llm_provider: provider };
  }
  return data;
}
