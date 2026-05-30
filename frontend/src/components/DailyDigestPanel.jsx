import { useState, useEffect, useCallback } from 'react';
import { getTodayDigest, generateDailyDigest, listDigests, getDigestByDate, getObsidianContent } from '../api/client';
import { withLLMProvider } from '../utils/llmProvider';
import toast from 'react-hot-toast';

const HEAT_COLORS = {
  '极高': 'bg-red-500/20 text-red-400 border-red-500/30',
  '高':   'bg-orange-500/20 text-orange-400 border-orange-500/30',
  '中':   'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  '低':   'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

const TIMING_COLORS = {
  '立即':   'bg-red-500/20 text-red-400',
  '今天内': 'bg-orange-500/20 text-orange-400',
  '本周内': 'bg-yellow-500/20 text-yellow-400',
};

const CATEGORY_ICONS = {
  '科技数码': '💻', '娱乐明星': '🎬', '社会民生': '🏛',
  '财经商业': '💰', '生活方式': '🌿', '教育职场': '📚',
  '体育竞技': '⚽', '游戏动漫': '🎮', '其他': '📌',
};

const TRACK_PRESETS = [
  { id: '科技', label: '💻 科技', desc: 'AI、手机、互联网' },
  { id: '美妆', label: '💄 美妆', desc: '护肤、彩妆、医美' },
  { id: '游戏', label: '🎮 游戏', desc: '手游、主机、电竞' },
  { id: '美食', label: '🍜 美食', desc: '探店、菜谱、食材' },
  { id: '健身', label: '💪 健身', desc: '运动、减脂、瑜伽' },
  { id: '教育', label: '📚 教育', desc: '考试、留学、职场' },
  { id: '财经', label: '📈 财经', desc: '股市、基金、理财' },
  { id: '汽车', label: '🚗 汽车', desc: '新能源、测评、自驾' },
  { id: '旅行', label: '✈️ 旅行', desc: '攻略、打卡、小众' },
  { id: '穿搭', label: '👗 穿搭', desc: 'OOTD、平价、潮流' },
];

export default function DailyDigestPanel() {
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [history, setHistory] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [obsidianContent, setObsidianContent] = useState('');
  const [showObsidian, setShowObsidian] = useState(false);
  const [selectedTrack, setSelectedTrack] = useState('');
  const [customTrack, setCustomTrack] = useState('');
  const [expandedTopics, setExpandedTopics] = useState(new Set());

  const loadToday = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTodayDigest();
      setDigest(res.data);
      setSelectedDate(null);
    } catch (e) {
      toast.error('加载失败: ' + e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const res = await listDigests(30);
      setHistory(res.items || []);
    } catch (e) {
      console.warn('加载历史失败:', e);
    }
  }, []);

  useEffect(() => { loadToday(); loadHistory(); }, [loadToday, loadHistory]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const data = {};
      const track = customTrack.trim() || selectedTrack;
      if (track) data.track = track;
      const res = await generateDailyDigest(withLLMProvider(data));
      setDigest(res.data);
      setSelectedDate(null);
      toast.success(track ? `「${track}」赛道热点已生成` : '热点总结已生成并同步到 Obsidian');
      loadHistory();
    } catch (e) {
      toast.error('生成失败: ' + e.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleSelectDate = async (date) => {
    setLoading(true);
    try {
      const res = await getDigestByDate(date);
      setDigest(res.data);
      setSelectedDate(date);
    } catch (e) {
      toast.error('加载失败: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleShowObsidian = async () => {
    const date = selectedDate || digest?.date;
    if (!date) return;
    try {
      const content = await getObsidianContent(date);
      setObsidianContent(content);
      setShowObsidian(true);
    } catch (e) {
      toast.error('Obsidian 文件不存在');
    }
  };

  const toggleTopicExpand = (key) => {
    setExpandedTopics(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const handleSelectTrack = (trackId) => {
    setSelectedTrack(prev => prev === trackId ? '' : trackId);
    setCustomTrack('');
  };

  if (loading && !digest) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="inline-block w-10 h-10 border-4 border-brand-500/30 border-t-brand-400 rounded-full animate-spin mb-4" />
          <p className="text-txt-secondary">加载热点总结中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页头 */}
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-txt-bright flex items-center gap-3">
            <span className="w-1 h-6 rounded-full bg-gradient-to-b from-amber-400 to-orange-600" />
            每日热点总结
          </h2>
          <p className="text-sm text-txt-secondary mt-1">
            聚合多平台热搜 · AI 深度分析 · 来源可追溯 · 同步 Obsidian
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 text-white font-medium text-sm shadow-lg shadow-amber-500/20 hover:shadow-amber-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {generating ? (
            <>
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              生成中...
            </>
          ) : (
            <>🔄 重新生成</>
          )}
        </button>
      </div>

      {/* 赛道选择器 */}
      <div className="card p-4">
        <h3 className="text-sm font-semibold text-txt-primary mb-3 flex items-center gap-2">
          <span className="w-1 h-4 rounded-full bg-brand-400" />
          🎯 赛道筛选
          {(selectedTrack || customTrack) && (
            <span className="px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-400 text-xs">
              当前：{customTrack || selectedTrack}
            </span>
          )}
        </h3>
        <div className="flex flex-wrap gap-2 mb-3">
          {TRACK_PRESETS.map(track => (
            <button
              key={track.id}
              onClick={() => handleSelectTrack(track.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedTrack === track.id
                  ? 'bg-brand-500/20 text-brand-400 border border-brand-500/40'
                  : 'bg-panel-100 text-txt-secondary border border-transparent hover:border-panel-border hover:text-txt-primary'
              }`}
            >
              {track.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={customTrack}
            onChange={(e) => { setCustomTrack(e.target.value); setSelectedTrack(''); }}
            placeholder="自定义赛道（如：宠物、母婴、家居）"
            className="flex-1 px-3 py-2 rounded-xl bg-panel-100 border border-panel-border text-txt-primary text-sm placeholder:text-txt-muted focus:border-brand-500/50 focus:outline-none transition-colors"
          />
          {(selectedTrack || customTrack) && (
            <button
              onClick={() => { setSelectedTrack(''); setCustomTrack(''); }}
              className="px-3 py-2 rounded-xl bg-panel-100 border border-panel-border text-txt-secondary text-sm hover:text-txt-primary transition-colors"
            >
              ✕ 清除
            </button>
          )}
        </div>
        <p className="text-[11px] text-txt-muted mt-2">
          💡 选择赛道后点击"重新生成"，AI 将只分析该赛道相关的热点，忽略其他内容
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* 主内容区 */}
        <div className="xl:col-span-3 space-y-6">
          {digest ? (
            <>
              {/* 今日概览 */}
              <div className="card p-6 border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-orange-500/5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-txt-primary flex items-center gap-2">
                    <span className="w-1 h-4 rounded-full bg-amber-400" />
                    📰 {digest.date} 概览
                  </h3>
                  <div className="flex items-center gap-2">
                    {digest.track && (
                      <span className="px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400 text-xs">
                        🏷️ {digest.track}赛道
                      </span>
                    )}
                    {digest.focus_topic && !digest.track && (
                      <span className="px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-400 text-xs">
                        🎯 {digest.focus_topic}
                      </span>
                    )}
                    <span className="text-xs text-txt-muted">
                      {digest.total_hot_items} 条热搜
                    </span>
                  </div>
                </div>
                <p className="text-txt-secondary leading-relaxed">{digest.overview}</p>
                <div className="flex gap-3 mt-4">
                  {Object.entries(digest.platform_stats || {}).map(([p, count]) => (
                    <span key={p} className="px-3 py-1 rounded-lg bg-panel-100 text-xs text-txt-secondary">
                      {p === 'bilibili' ? 'B站' : p === 'douyin' ? '抖音' : p === 'xiaohongshu' ? '小红书' : '微博'}: {count}条
                    </span>
                  ))}
                </div>
              </div>

              {/* 热点分类 */}
              {digest.categories?.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-txt-primary flex items-center gap-2">
                    <span className="w-1 h-4 rounded-full bg-brand-400" />
                    🔖 热点分类
                  </h3>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {digest.categories.map((cat, ci) => (
                      <div key={ci} className="card p-4">
                        <h4 className="text-sm font-semibold text-txt-primary mb-3 flex items-center gap-2">
                          <span>{cat.icon || CATEGORY_ICONS[cat.name] || '📌'}</span>
                          <span>{cat.name}</span>
                          <span className="text-xs text-txt-muted ml-auto">{cat.topics?.length || 0} 条</span>
                        </h4>
                        <div className="space-y-2 max-h-80 overflow-y-auto">
                          {cat.topics?.map((t, ti) => {
                            const topicKey = `${ci}-${ti}`;
                            const isExpanded = expandedTopics.has(topicKey);
                            return (
                              <div
                                key={ti}
                                className="p-2.5 rounded-xl bg-panel-100/50 hover:bg-panel-100 transition-colors cursor-pointer"
                                onClick={() => toggleTopicExpand(topicKey)}
                              >
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-sm font-medium text-txt-primary">{t.topic}</span>
                                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${HEAT_COLORS[t.heat] || HEAT_COLORS['中']}`}>
                                    {t.heat}
                                  </span>
                                </div>
                                <p className="text-xs text-txt-secondary leading-relaxed">{t.summary}</p>

                                {/* 来源链接 */}
                                {t.platforms?.length > 0 && (
                                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                                    {t.platforms.map((p, pi) => {
                                      const url = t.urls?.[p];
                                      return url ? (
                                        <a
                                          key={pi}
                                          href={url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px] hover:bg-blue-500/20 transition-colors"
                                          onClick={(e) => e.stopPropagation()}
                                        >
                                          🔗 {p}
                                        </a>
                                      ) : (
                                        <span key={pi} className="px-1.5 py-0.5 rounded bg-panel-50 text-[10px] text-txt-muted">
                                          {p}
                                        </span>
                                      );
                                    })}
                                  </div>
                                )}

                                {/* AI 观点（展开时显示） */}
                                {isExpanded && t.ai_take && (
                                  <div className="mt-2 p-2 rounded-lg bg-purple-500/5 border border-purple-500/10">
                                    <p className="text-[11px] text-purple-300 leading-relaxed">
                                      🧠 <em>{t.ai_take}</em>
                                    </p>
                                  </div>
                                )}
                                {isExpanded && t.content_angle && (
                                  <p className="text-xs text-brand-400 mt-1.5">
                                    💡 {t.content_angle}
                                  </p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 跨平台热点 */}
              {digest.cross_platform?.length > 0 && (
                <div className="card p-5">
                  <h3 className="text-sm font-semibold text-txt-primary mb-4 flex items-center gap-2">
                    <span className="w-1 h-4 rounded-full bg-red-400" />
                    🔥 跨平台热点
                  </h3>
                  <div className="space-y-3">
                    {digest.cross_platform.map((item, i) => (
                      <div key={i} className="p-3 rounded-xl bg-gradient-to-r from-red-500/5 to-orange-500/5 border border-red-500/10">
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className="text-sm font-semibold text-txt-primary">{item.topic}</span>
                          <div className="flex gap-1">
                            {item.platforms?.map((p, pi) => {
                              const url = item.urls?.[p];
                              return url ? (
                                <a
                                  key={pi}
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 text-[10px] font-medium hover:bg-red-500/30 transition-colors"
                                >
                                  🔗 {p}
                                </a>
                              ) : (
                                <span key={pi} className="px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 text-[10px] font-medium">
                                  {p}
                                </span>
                              );
                            })}
                          </div>
                        </div>
                        <p className="text-xs text-txt-secondary mb-1.5">{item.analysis}</p>
                        {item.ai_take && (
                          <p className="text-[11px] text-purple-300">
                            🧠 <em>{item.ai_take}</em>
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 创作机会 */}
              {digest.opportunities?.length > 0 && (
                <div className="card p-5">
                  <h3 className="text-sm font-semibold text-txt-primary mb-4 flex items-center gap-2">
                    <span className="w-1 h-4 rounded-full bg-emerald-400" />
                    💡 创作机会
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {digest.opportunities.map((opp, i) => (
                      <div key={i} className="p-4 rounded-xl bg-panel-100/50 border border-panel-border hover:border-brand-500/30 transition-colors">
                        <h4 className="text-sm font-semibold text-txt-primary mb-2">{opp.title}</h4>
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          <span className="px-2 py-0.5 rounded bg-brand-500/20 text-brand-400 text-[10px]">{opp.platform}</span>
                          <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 text-[10px]">{opp.format}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] ${TIMING_COLORS[opp.timing] || 'bg-slate-500/20 text-slate-400'}`}>
                            ⏰ {opp.timing}
                          </span>
                        </div>
                        <p className="text-xs text-txt-secondary leading-relaxed">{opp.angle}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 趋势洞察 */}
              {digest.insights?.length > 0 && (
                <div className="card p-5">
                  <h3 className="text-sm font-semibold text-txt-primary mb-4 flex items-center gap-2">
                    <span className="w-1 h-4 rounded-full bg-purple-400" />
                    🔮 趋势洞察
                  </h3>
                  <div className="space-y-3">
                    {digest.insights.map((ins, i) => (
                      <div key={i} className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/10">
                        <p className="text-sm font-medium text-txt-primary mb-1">{ins.pattern}</p>
                        <p className="text-xs text-txt-secondary">👉 {ins.implication}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI 主编手记 */}
              {digest.ai_commentary && (
                <div className="card p-6 border-purple-500/20 bg-gradient-to-br from-purple-500/5 to-indigo-500/5">
                  <h3 className="text-sm font-semibold text-txt-primary mb-4 flex items-center gap-2">
                    <span className="w-1 h-4 rounded-full bg-purple-400" />
                    🖊️ AI 主编手记
                  </h3>
                  <div className="prose prose-invert prose-sm max-w-none">
                    {digest.ai_commentary.split('\n').filter(Boolean).map((para, i) => (
                      <p key={i} className="text-txt-secondary leading-relaxed text-sm mb-3">{para}</p>
                    ))}
                  </div>
                  <p className="text-[10px] text-txt-muted mt-4 border-t border-panel-border pt-3">
                    * 以上内容由 AI 基于今日热搜数据独立撰写，代表 AI 的分析观点，仅供参考
                  </p>
                </div>
              )}

              {/* Obsidian 同步状态 */}
              <div className="card p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-lg">📓</span>
                  <div>
                    <p className="text-sm font-medium text-txt-primary">Obsidian 同步</p>
                    <p className="text-xs text-txt-muted">
                      {digest.obsidian_path ? `已保存至 ${digest.obsidian_path}` : '生成时自动同步'}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleShowObsidian}
                    className="px-3 py-1.5 rounded-lg bg-panel-100 border border-panel-border text-xs text-txt-secondary hover:text-txt-primary hover:border-brand-500/30 transition-colors"
                  >
                    📄 查看 Markdown
                  </button>
                </div>
              </div>

              {/* Obsidian 预览弹窗 */}
              {showObsidian && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowObsidian(false)}>
                  <div className="w-full max-w-3xl max-h-[80vh] bg-panel-50 rounded-2xl border border-panel-border shadow-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-between px-5 py-3 border-b border-panel-border">
                      <h3 className="text-sm font-semibold text-txt-primary">📓 Obsidian Markdown 预览</h3>
                      <button onClick={() => setShowObsidian(false)} className="text-txt-muted hover:text-txt-primary text-lg">×</button>
                    </div>
                    <pre className="p-5 overflow-auto max-h-[calc(80vh-60px)] text-xs text-txt-secondary font-mono leading-relaxed whitespace-pre-wrap">
                      {obsidianContent}
                    </pre>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="card p-16 text-center">
              <p className="text-5xl mb-4">📰</p>
              <p className="text-txt-secondary mb-2">选择赛道后点击"重新生成"获取热点总结</p>
              <p className="text-xs text-txt-muted mb-4">不选赛道则生成全量热点</p>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 text-white font-medium shadow-lg"
              >
                {generating ? '生成中...' : '🔄 生成今日热点'}
              </button>
            </div>
          )}
        </div>

        {/* 右侧历史栏 */}
        <div className="space-y-4">
          <div className="card p-4">
            <h3 className="text-sm font-semibold text-txt-primary mb-3 flex items-center gap-2">
              <span className="w-1 h-4 rounded-full bg-amber-400" />
              📅 历史记录
            </h3>
            {history.length === 0 ? (
              <p className="text-xs text-txt-muted">暂无历史记录</p>
            ) : (
              <div className="space-y-1.5 max-h-[60vh] overflow-y-auto">
                <button
                  onClick={() => { setSelectedDate(null); loadToday(); }}
                  className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-colors ${
                    !selectedDate
                      ? 'bg-brand-500/15 text-brand-400 border border-brand-500/20'
                      : 'text-txt-secondary hover:bg-panel-100'
                  }`}
                >
                  <div className="font-medium">📍 今日</div>
                  <div className="text-xs text-txt-muted mt-0.5">{new Date().toLocaleDateString('zh-CN')}</div>
                </button>
                {history.map((h, i) => (
                  <button
                    key={i}
                    onClick={() => handleSelectDate(h.date)}
                    className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-colors ${
                      selectedDate === h.date
                        ? 'bg-brand-500/15 text-brand-400 border border-brand-500/20'
                        : 'text-txt-secondary hover:bg-panel-100'
                    }`}
                  >
                    <div className="font-medium">{h.date}</div>
                    <div className="text-xs text-txt-muted mt-0.5 line-clamp-2">{h.overview}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-txt-muted">{h.total_hot_items} 条热搜</span>
                      {h.track && (
                        <span className="text-[10px] text-purple-400">🏷️ {h.track}</span>
                      )}
                      {h.focus_topic && !h.track && (
                        <span className="text-[10px] text-brand-400">🎯 {h.focus_topic}</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
