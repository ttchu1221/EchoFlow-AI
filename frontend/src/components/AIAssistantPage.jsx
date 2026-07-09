import { useState, useRef, useEffect, useCallback } from 'react';
import {
  getConversations,
  createConversation,
  getConversation,
  deleteConversation,
  updateConversation,
  chatStream,
} from '../api/client';

export default function AIAssistantPage() {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [loadingConvList, setLoadingConvList] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [editingTitle, setEditingTitle] = useState(null);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const abortRef = useRef(null);

  // 加载对话列表
  const loadConversations = useCallback(async () => {
    try {
      setLoadingConvList(true);
      const result = await getConversations();
      setConversations(result.conversations || []);
    } catch (e) {
      console.error('加载对话列表失败:', e);
    } finally {
      setLoadingConvList(false);
    }
  }, []);

  // 加载对话详情（含消息历史）
  const loadConversation = useCallback(async (convId) => {
    try {
      setLoadingMessages(true);
      const result = await getConversation(convId);
      setMessages(result.messages || []);
    } catch (e) {
      console.error('加载对话详情失败:', e);
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // 切换对话时自动加载消息
  useEffect(() => {
    if (activeConvId) {
      loadConversation(activeConvId);
    } else {
      setMessages([]);
    }
  }, [activeConvId, loadConversation]);

  // 自动滚动到底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  // 新建对话
  const handleNewConversation = async () => {
    try {
      const result = await createConversation({ title: '新对话' });
      const conv = result.conversation || result;
      await loadConversations();
      setActiveConvId(conv._id || conv.id);
      inputRef.current?.focus();
    } catch (e) {
      console.error('新建对话失败:', e);
    }
  };

  // 删除对话
  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (!confirm('确定删除此对话？')) return;
    try {
      await deleteConversation(convId);
      if (activeConvId === convId) {
        setActiveConvId(null);
      }
      await loadConversations();
    } catch (e) {
      console.error('删除对话失败:', e);
    }
  };

  // 重命名对话
  const handleRename = async (convId, newTitle) => {
    try {
      await updateConversation(convId, { title: newTitle });
      setEditingTitle(null);
      await loadConversations();
    } catch (e) {
      console.error('重命名失败:', e);
    }
  };

  // 发送消息
  const handleSend = async () => {
    const text = input.trim();
    if (!text || streaming) return;

    let convId = activeConvId;

    // 如果没有活跃对话，先创建
    if (!convId) {
      try {
        const result = await createConversation({ title: text.slice(0, 30) });
        const conv = result.conversation || result;
        convId = conv._id || conv.id;
        setActiveConvId(convId);
        await loadConversations();
      } catch (e) {
        console.error('创建对话失败:', e);
        return;
      }
    }

    // 添加用户消息到本地
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setInput('');
    setStreaming(true);
    setStreamingText('');

    let fullText = '';

    abortRef.current = chatStream(
      convId,
      text,
      // onToken
      (token) => {
        fullText += token;
        setStreamingText(fullText);
      },
      // onDone
      (data) => {
        setStreaming(false);
        setStreamingText('');
        if (fullText) {
          setMessages(prev => [...prev, { role: 'assistant', content: fullText }]);
        }
        loadConversations(); // 刷新列表（更新标题等）
      },
      // onError
      (err) => {
        console.error('流式对话错误:', err);
        setStreaming(false);
        setStreamingText('');
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: `⚠️ 发生错误: ${err.message}` },
        ]);
      },
    );
  };

  // 停止生成
  const handleStop = () => {
    abortRef.current?.();
    setStreaming(false);
    setStreamingText('');
  };

  // 渲染消息内容（简易 Markdown）
  const renderContent = (text) => {
    if (!text) return null;
    const parts = text.split(/(```[\s\S]*?```|`[^`]+`|\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const code = part.slice(3, -3).replace(/^\w+\n/, '');
        return (
          <pre key={i} className="bg-panel-100 border border-panel-border rounded-xl p-3 my-2 text-xs text-brand-300 overflow-x-auto whitespace-pre-wrap break-words font-mono">
            {code}
          </pre>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={i} className="bg-panel-100 px-1.5 py-0.5 rounded text-xs text-brand-300 font-mono">
            {part.slice(1, -1)}
          </code>
        );
      }
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
      }
      // 普通文本按换行拆分
      return part.split('\n').map((line, j) => (
        <span key={`${i}-${j}`}>
          {line}
          {j < part.split('\n').length - 1 && <br />}
        </span>
      ));
    });
  };

  const activeConv = conversations.find(c => (c._id || c.id) === activeConvId);

  return (
    <div className="dashboard-container h-screen flex">
      {/* ── 左侧：对话列表 ── */}
      <div className={`${sidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 flex-shrink-0 overflow-hidden border-r border-panel-border bg-panel-50/60`}>
        <div className="w-72 h-full flex flex-col">
          {/* 头部 */}
          <div className="p-4 border-b border-panel-border">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-bold text-white">💬 AI 助手</h2>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-1 rounded-lg text-txt-muted hover:text-brand-400 hover:bg-panel-100 transition-colors lg:hidden"
                title="收起"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
                </svg>
              </button>
            </div>
            <button
              onClick={handleNewConversation}
              className="w-full px-3 py-2.5 rounded-xl text-sm font-medium bg-brand-500 hover:bg-brand-600 text-white transition-colors flex items-center justify-center gap-2"
            >
              <span>+</span> 新对话
            </button>
          </div>

          {/* 列表 */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {loadingConvList ? (
              <div className="p-4 text-center text-txt-muted text-sm">加载中...</div>
            ) : conversations.length === 0 ? (
              <div className="p-4 text-center text-txt-muted text-xs">暂无对话，点击上方新建</div>
            ) : (
              conversations.map(conv => {
                const convId = conv._id || conv.id;
                const isActive = convId === activeConvId;
                const isEditing = editingTitle === convId;
                return (
                  <div
                    key={convId}
                    onClick={() => !isEditing && setActiveConvId(convId)}
                    className={`group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all ${
                      isActive
                        ? 'bg-brand-500/15 text-brand-300'
                        : 'text-txt-secondary hover:bg-panel-100'
                    }`}
                  >
                    <span className="text-base flex-shrink-0">💬</span>
                    <div className="flex-1 min-w-0">
                      {isEditing ? (
                        <input
                          autoFocus
                          defaultValue={conv.title}
                          onBlur={e => handleRename(convId, e.target.value)}
                          onKeyDown={e => {
                            if (e.key === 'Enter') handleRename(convId, e.target.value);
                            if (e.key === 'Escape') setEditingTitle(null);
                          }}
                          onClick={e => e.stopPropagation()}
                          className="w-full bg-transparent text-sm text-white outline-none border-b border-brand-500"
                        />
                      ) : (
                        <p
                          className="text-sm truncate"
                          onDoubleClick={e => { e.stopPropagation(); setEditingTitle(convId); }}
                          title={conv.title}
                        >
                          {conv.title || '未命名对话'}
                        </p>
                      )}
                      <p className="text-xs text-txt-muted mt-0.5">
                        {conv.message_count || 0} 条消息
                        {conv.updated_at && ` · ${new Date(conv.updated_at).toLocaleDateString()}`}
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(convId, e)}
                      className="p-1 rounded text-txt-muted hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                      title="删除"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* ── 右侧：对话区 ── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 顶部栏 */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-panel-border bg-panel-50/40 backdrop-blur-sm flex-shrink-0">
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-lg text-txt-muted hover:text-brand-400 hover:bg-panel-100 transition-colors"
              title="展开侧边栏"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </button>
          )}
          <h2 className="text-sm font-bold text-white truncate">
            {activeConv ? activeConv.title : 'AI 对话助手'}
          </h2>
          {activeConv && (
            <span className="text-xs text-txt-muted">
              {activeConv.message_count || messages.length} 条消息 · 有长期记忆
            </span>
          )}
        </div>

        {/* 消息区 */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {!activeConvId && !streaming && messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-2xl bg-brand-500/10 flex items-center justify-center text-3xl mb-4 shadow-[0_0_20px_rgba(34,211,238,0.15)]">
                🤖
              </div>
              <h3 className="text-lg font-bold text-white mb-2">EchoFlow AI 助手</h3>
              <p className="text-sm text-txt-secondary max-w-md mb-6">
                拥有长短期记忆的智能对话助手。支持上下文理解和会话连续性，帮助你高效完成各类任务。
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
                {[
                  { icon: '📝', text: '帮我写一份内容创作策略', tip: '我可以基于你的目标制定详细计划' },
                  { icon: '📊', text: '分析最近的数据趋势', tip: '我可以帮你解读数据并给出建议' },
                  { icon: '💡', text: '头脑风暴新选题', tip: '我可以提供创意灵感和选题建议' },
                  { icon: '🔍', text: '优化现有内容方案', tip: '我可以帮你诊断并优化方案' },
                ].map((item, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setInput(item.text);
                      inputRef.current?.focus();
                    }}
                    className="p-3 rounded-xl bg-panel-100/50 border border-panel-border hover:border-brand-500/30 hover:bg-panel-100 text-left transition-all group"
                  >
                    <span className="text-base">{item.icon}</span>
                    <p className="text-sm text-white mt-1.5">{item.text}</p>
                    <p className="text-xs text-txt-muted mt-1">{item.tip}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 消息列表 */}
          {(messages.length > 0 || streaming) && messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-brand-500/15 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                  🤖
                </div>
              )}
              <div
                className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-brand-500 text-white rounded-br-md'
                    : 'bg-panel-100 border border-panel-border text-txt-primary rounded-bl-md'
                }`}
              >
                {renderContent(msg.content)}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-panel-200 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                  👤
                </div>
              )}
            </div>
          ))}

          {/* 流式消息 */}
          {streaming && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-lg bg-brand-500/15 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                🤖
              </div>
              <div className="max-w-[75%] px-4 py-3 rounded-2xl bg-panel-100 border border-panel-border text-txt-primary rounded-bl-md">
                {streamingText ? (
                  <div className="text-sm leading-relaxed">
                    {renderContent(streamingText)}
                    <span className="inline-block w-1.5 h-4 bg-brand-400 ml-0.5 animate-pulse align-middle" />
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 py-1">
                    <span className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                )}
              </div>
            </div>
          )}

          {loadingMessages && (
            <div className="text-center py-4 text-txt-muted text-sm">加载消息历史...</div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* ── 底部输入框 ── */}
        <div className="flex-shrink-0 px-4 py-3 border-t border-panel-border bg-panel-50/40 backdrop-blur-sm">
          <div className="flex items-end gap-3 max-w-4xl mx-auto">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (streaming) handleStop();
                    else handleSend();
                  }
                }}
                placeholder={streaming ? 'AI 正在回复...' : '输入消息，Shift+Enter 换行，Enter 发送...'}
                disabled={streaming}
                rows={1}
                className="w-full px-4 py-3 bg-panel-100 border border-panel-border rounded-xl text-white text-sm resize-none focus:border-brand-500 focus:outline-none placeholder:text-txt-muted disabled:opacity-50"
                style={{ minHeight: '44px', maxHeight: '120px' }}
                onInput={e => {
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                }}
              />
            </div>
            {streaming ? (
              <button
                onClick={handleStop}
                className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 hover:bg-red-500/20 transition-colors flex-shrink-0"
                title="停止生成"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="px-4 py-3 rounded-xl bg-brand-500 hover:bg-brand-600 text-white transition-colors disabled:opacity-30 flex-shrink-0"
                title="发送"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                </svg>
              </button>
            )}
          </div>
          <p className="text-xs text-txt-muted text-center mt-2">
            AI 助手具备长短期记忆 · 自动压缩历史上下文 · 模型可在设置中切换
          </p>
        </div>
      </div>
    </div>
  );
}
