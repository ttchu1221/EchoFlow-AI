import { useState, useEffect } from 'react';
import { getPlatforms } from '../api/client';

const API_BASE = '/api/platform';

function formatNumber(num) {
  if (!num && num !== 0) return '0';
  num = Number(num) || 0;
  if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
  if (num >= 10000) return (num / 10000).toFixed(1) + '万';
  return num.toLocaleString();
}

const PROVIDERS = [
  { id: 'douyin', name: '抖音', icon: '🎵', color: 'brand' },
  { id: 'xiaohongshu', name: '小红书', icon: '📕', color: 'red' },
  { id: 'bilibili', name: 'B站', icon: '📺', color: 'blue' },
  { id: 'kuaishou', name: '快手', icon: '🎬', color: 'amber' },
  { id: 'weibo', name: '微博', icon: '🔥', color: 'orange' },
];

export default function PlatformSyncPanel() {
  const [collected, setCollected] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [platforms, setPlatforms] = useState([]);

  useEffect(() => {
    getPlatforms().then(setPlatforms).catch(() => {});
  }, []);

  const fetchCollected = async (p = 1) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/collect/list?page=${p}&size=20`);
      if (res.ok) {
        const data = await res.json();
        setCollected(data.items || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('获取数据失败:', err);
    }
    setLoading(false);
  };

  useEffect(() => { fetchCollected(page); }, [page]);

  const today = new Date().toISOString().slice(0, 10);
  const todayCount = collected.filter(v => v.collected_at?.startsWith(today)).length;

  const colorMap = {
    brand: { bg: 'bg-brand-500/15', border: 'border-brand-500/30', text: 'text-brand-300', badge: 'bg-brand-500/20 text-brand-300' },
    red:   { bg: 'bg-red-500/15', border: 'border-red-500/30', text: 'text-red-300', badge: 'bg-red-500/20 text-red-300' },
    blue:  { bg: 'bg-blue-500/15', border: 'border-blue-500/30', text: 'text-blue-300', badge: 'bg-blue-500/20 text-blue-300' },
    amber: { bg: 'bg-amber-500/15', border: 'border-amber-500/30', text: 'text-amber-300', badge: 'bg-amber-500/20 text-amber-300' },
    orange:{ bg: 'bg-orange-500/15', border: 'border-orange-500/30', text: 'text-orange-300', badge: 'bg-orange-500/20 text-orange-300' },
  };

  return (
    <div className="dashboard-container min-h-screen p-6">
      {/* 标题 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white dashboard-glow-text">⭐ 爆款采集</h1>
        <p className="text-txt-secondary mt-1">浏览抖音时点击右侧 ⭐ 按钮，一键采集爆款视频</p>
      </div>

      {/* 平台卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
        {PROVIDERS.map(p => (
          <div
            key={p.id}
            className={`dashboard-panel rounded-2xl p-4 text-center border ${colorMap[p.color]?.border || 'border-panel-border'}`}
          >
            <div className="text-3xl mb-2">{p.icon}</div>
            <p className="text-sm font-medium text-white">{p.name}</p>
            <span className={`inline-block mt-2 px-2.5 py-0.5 rounded-lg text-xs font-medium ${colorMap[p.color]?.badge || 'tag-gray'}`}>
              已连接
            </span>
          </div>
        ))}
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="dashboard-panel rounded-2xl p-5 text-center border border-brand-500/30">
          <div className="text-3xl font-bold text-brand-300 mb-1">{total}</div>
          <p className="text-xs text-txt-muted">总采集</p>
        </div>
        <div className="dashboard-panel rounded-2xl p-5 text-center border border-emerald-500/30">
          <div className="text-3xl font-bold text-emerald-300 mb-1">{todayCount}</div>
          <p className="text-xs text-txt-muted">今日采集</p>
        </div>
        <div className="dashboard-panel rounded-2xl p-5 text-center border border-purple-500/30">
          <div className="text-3xl font-bold text-purple-300 mb-1">
            {collected.filter(v => v.platform === 'douyin').length}
          </div>
          <p className="text-xs text-txt-muted">抖音</p>
        </div>
      </div>

      {/* 使用说明 */}
      <div className="dashboard-panel rounded-2xl p-6 mb-6 border border-brand-500/20">
        <h3 className="text-lg font-bold text-white mb-3">📖 使用方法</h3>
        <ol className="text-sm text-txt-secondary leading-loose pl-5 list-decimal space-y-1">
          <li>安装浏览器插件（<code className="bg-panel-100 px-2 py-0.5 rounded text-brand-300 text-xs font-mono">extensions/douyin</code>）</li>
          <li>打开 <a href="https://www.douyin.com" target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:underline">douyin.com</a> 浏览视频</li>
          <li>看到爆款视频 → 点击页面右侧的 <strong className="text-white">⭐</strong> 按钮</li>
          <li>视频自动保存到此处</li>
        </ol>
      </div>

      {/* 采集列表 */}
      <div className="dashboard-panel rounded-2xl p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-white">📝 采集记录 ({total})</h2>
          <button
            onClick={() => fetchCollected(page)}
            className="btn-secondary text-xs px-3 py-1.5"
          >
            🔄 刷新
          </button>
        </div>

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="shimmer h-14 rounded-xl" />
            ))}
          </div>
        ) : collected.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">📭</div>
            <p className="text-txt-secondary mb-1">暂无采集记录</p>
            <p className="text-xs text-txt-muted">安装插件后浏览抖音，点击 ⭐ 按钮开始采集</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-panel-border">
                    <th className="py-3 px-3 text-left text-xs font-semibold text-txt-muted uppercase tracking-wider">标题</th>
                    <th className="py-3 px-3 text-left text-xs font-semibold text-txt-muted uppercase tracking-wider">作者</th>
                    <th className="py-3 px-3 text-right text-xs font-semibold text-txt-muted uppercase tracking-wider">❤️ 点赞</th>
                    <th className="py-3 px-3 text-right text-xs font-semibold text-txt-muted uppercase tracking-wider">💬 评论</th>
                    <th className="py-3 px-3 text-right text-xs font-semibold text-txt-muted uppercase tracking-wider">⭐ 收藏</th>
                    <th className="py-3 px-3 text-right text-xs font-semibold text-txt-muted uppercase tracking-wider">🔗 转发</th>
                    <th className="py-3 px-3 text-center text-xs font-semibold text-txt-muted uppercase tracking-wider">链接</th>
                  </tr>
                </thead>
                <tbody>
                  {collected.map((v, i) => (
                    <tr
                      key={i}
                      className="border-b border-panel-border/50 hover:bg-panel-100/50 transition-colors"
                    >
                      <td className="py-3 px-3 max-w-[250px] truncate text-white">
                        {v.title || '未命名'}
                      </td>
                      <td className="py-3 px-3 text-txt-secondary text-xs">{v.author || '-'}</td>
                      <td className="py-3 px-3 text-right font-mono text-emerald-300 text-xs">{formatNumber(v.likes)}</td>
                      <td className="py-3 px-3 text-right font-mono text-blue-300 text-xs">{formatNumber(v.comments)}</td>
                      <td className="py-3 px-3 text-right font-mono text-amber-300 text-xs">{formatNumber(v.collects)}</td>
                      <td className="py-3 px-3 text-right font-mono text-purple-300 text-xs">{formatNumber(v.shares)}</td>
                      <td className="py-3 px-3 text-center">
                        {v.url ? (
                          <a
                            href={v.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-brand-400 hover:text-brand-300 transition-colors"
                            title="打开链接"
                          >
                            🔗
                          </a>
                        ) : (
                          <span className="text-txt-muted">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 分页 */}
            {total > 20 && (
              <div className="flex items-center justify-center gap-3 mt-5 pt-4 border-t border-panel-border">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-xs px-4 py-1.5 disabled:opacity-30"
                >
                  ← 上一页
                </button>
                <span className="text-xs text-txt-muted">
                  {page} / {Math.ceil(total / 20)}
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= Math.ceil(total / 20)}
                  className="btn-secondary text-xs px-4 py-1.5 disabled:opacity-30"
                >
                  下一页 →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
