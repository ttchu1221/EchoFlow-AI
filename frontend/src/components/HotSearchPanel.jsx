import { useState, useEffect } from 'react';
import { getHotSearch } from '../api/client';
import DashboardChart, { NEON_COLORS } from './DashboardChart';
import StatsCard from './StatsCard';

const PLATFORMS = [
  { id: 'bilibili',    label: 'B站',    color: 'from-blue-400 to-blue-600',  neon: 'cyan' },
  { id: 'douyin',      label: '抖音',   color: 'from-gray-600 to-gray-800',  neon: 'purple' },
  { id: 'xiaohongshu', label: '小红书', color: 'from-red-400 to-pink-600',   neon: 'pink' },
  { id: 'weibo',       label: '微博',   color: 'from-orange-400 to-red-500', neon: 'amber' },
];

export default function HotSearchPanel() {
  const [platform, setPlatform] = useState('bilibili');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastUpdate, setLastUpdate] = useState('');

  const fetchHot = async (p) => {
    setLoading(true);
    setError('');
    try {
      const data = await getHotSearch(p, 30);
      setItems(data.items || []);
      setLastUpdate(new Date().toLocaleTimeString('zh-CN'));
    } catch (e) {
      setError(e.message);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHot(platform); }, [platform]);

  const currentPlatform = PLATFORMS.find(p => p.id === platform);

  /* ── 图表数据 ──────────────────────────────────── */
  const top15 = items.slice(0, 15);
  const barOption = {
    grid: { left: 120, right: 40, top: 10, bottom: 30 },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category',
      data: top15.map((_, i) => `#${i + 1}`).reverse(),
      axisLabel: { color: '#64748b', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: top15.map((item, i) => ({
        value: item.heat_score || 0,
        name: item.keyword,
      })).reverse(),
      barWidth: 14,
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: (params) => {
          const idx = params.dataIndex;
          const r = top15.length - 1 - idx;
          if (r < 3) return { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: 'rgba(34,211,238,0.1)' }, { offset: 1, color: '#22d3ee' }] };
          if (r < 6) return { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.1)' }, { offset: 1, color: '#3b82f6' }] };
          return { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: 'rgba(100,116,139,0.1)' }, { offset: 1, color: '#475569' }] };
        },
      },
      label: {
        show: true,
        position: 'right',
        formatter: (p) => p.data.name || '',
        color: '#94a3b8',
        fontSize: 11,
      },
    }],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const d = params[0];
        const item = top15[top15.length - 1 - d.dataIndex];
        return `<div style="font-size:13px;font-weight:600;color:#e2e8f0">${item?.keyword || ''}</div>
                <div style="font-size:12px;color:#94a3b8;margin-top:4px">热度: ${(d.value || 0).toLocaleString()}</div>`;
      },
    },
  };

  const rankPieOption = {
    series: [{
      type: 'pie',
      radius: ['55%', '75%'],
      center: ['50%', '50%'],
      data: [
        { value: items.filter((_, i) => i < 3).length, name: 'TOP 3', itemStyle: { color: '#22d3ee' } },
        { value: items.filter((_, i) => i >= 3 && i < 10).length, name: 'TOP 10', itemStyle: { color: '#3b82f6' } },
        { value: items.filter((_, i) => i >= 10).length, name: '其他', itemStyle: { color: '#475569' } },
      ].filter(d => d.value > 0),
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 13, fontWeight: 'bold', color: '#e2e8f0' },
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(34, 211, 238, 0.3)' },
      },
      itemStyle: { borderColor: '#0d1117', borderWidth: 2 },
    }],
    tooltip: { trigger: 'item', formatter: '{b}: {c} 条 ({d}%)' },
  };

  const avgHeat = items.length > 0 ? Math.round(items.reduce((s, i) => s + (i.heat_score || 0), 0) / items.length) : 0;
  const maxHeat = items.length > 0 ? Math.max(...items.map(i => i.heat_score || 0)) : 0;
  const hotCount = items.filter(i => (i.heat_score || 0) > avgHeat).length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页头 */}
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold text-txt-bright flex items-center gap-3">
            <span className="w-1 h-6 rounded-full bg-gradient-to-b from-brand-400 to-brand-600" />
            实时热搜
          </h2>
          <p className="text-sm text-txt-secondary mt-1">聚合多平台热榜数据，实时追踪内容趋势</p>
        </div>
        {lastUpdate && (
          <span className="text-xs text-txt-muted flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-soft" />
            更新于 {lastUpdate}
          </span>
        )}
      </div>

      {/* 平台切换 */}
      <div className="flex gap-2">
        {PLATFORMS.map((p) => (
          <button
            key={p.id}
            onClick={() => setPlatform(p.id)}
            className={`
              px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
              ${platform === p.id
                ? `bg-gradient-to-r ${p.color} text-white shadow-lg`
                : 'bg-panel-50 text-txt-secondary border border-panel-border hover:border-brand-500/30 hover:text-txt-primary'
              }
            `}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="card p-4 border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">⚠️ {error}</p>
          <p className="text-xs text-red-400/60 mt-1">请确保后端已启动，且网络可访问聚合数据源</p>
        </div>
      )}

      {/* 骨架屏 */}
      {loading ? (
        <div className="grid gap-3">
          <div className="shimmer h-80 rounded-2xl" />
          <div className="grid grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, i) => <div key={i} className="shimmer h-24 rounded-2xl" />)}
          </div>
        </div>
      ) : items.length > 0 ? (
        <>
          {/* 统计卡片 */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <StatsCard label="热搜总数" value={items.length} icon="📊" color="cyan" />
            <StatsCard label="平均热度" value={avgHeat} icon="🔥" color="amber" />
            <StatsCard label="最高热度" value={maxHeat} icon="🚀" color="red" />
            <StatsCard label="超均值" value={hotCount} unit="条" icon="📈" color="green" />
          </div>

          {/* 图表区 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 card p-4">
              <h3 className="text-sm font-semibold text-txt-primary mb-3 flex items-center gap-2">
                <span className="w-1 h-4 rounded-full bg-brand-400" />
                TOP 15 热度排行
              </h3>
              <DashboardChart option={barOption} height={420} />
            </div>
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-txt-primary mb-3 flex items-center gap-2">
                <span className="w-1 h-4 rounded-full bg-purple-400" />
                排名分布
              </h3>
              <DashboardChart option={rankPieOption} height={250} />
              {/* 前3名列表 */}
              <div className="mt-3 space-y-2">
                {items.slice(0, 3).map((item, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-panel-100/50">
                    <span className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold text-white ${
                      i === 0 ? 'bg-gradient-to-br from-amber-400 to-amber-600' :
                      i === 1 ? 'bg-gradient-to-br from-slate-300 to-slate-500' :
                      'bg-gradient-to-br from-amber-600 to-amber-800'
                    }`}>{i + 1}</span>
                    <span className="text-sm text-txt-primary truncate flex-1">{item.keyword}</span>
                    <span className="text-xs text-neon-amber font-mono">
                      {item.heat_score > 10000 ? (item.heat_score / 10000).toFixed(1) + '万' : item.heat_score?.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 完整列表 */}
          <div className="card overflow-hidden">
            <div className="px-5 py-3 border-b border-panel-border flex items-center justify-between">
              <h3 className="text-sm font-semibold text-txt-primary">完整热搜榜单</h3>
              <span className="text-xs text-txt-muted">{items.length} 条</span>
            </div>
            <div className="divide-y divide-panel-border/50 max-h-96 overflow-y-auto">
              {items.map((item, i) => (
                <div key={i} className="flex items-center gap-4 px-5 py-3 hover:bg-panel-100/50 transition-colors group">
                  <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                    i < 3 ? 'bg-gradient-to-br from-brand-400 to-brand-600 text-white shadow-neon-cyan' :
                    i < 10 ? 'bg-panel-100 text-brand-400 border border-brand-500/20' :
                    'bg-panel-100 text-txt-muted'
                  }`}>{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <a href={item.url} target="_blank" rel="noopener noreferrer"
                      className="text-sm text-txt-primary hover:text-brand-400 transition-colors truncate block">
                      {item.keyword}
                    </a>
                  </div>
                  {item.heat_score > 0 && (
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span className="text-xs">🔥</span>
                      <span className="text-xs font-mono text-neon-amber">
                        {item.heat_score > 10000 ? (item.heat_score / 10000).toFixed(1) + '万' : item.heat_score.toLocaleString()}
                      </span>
                    </div>
                  )}
                  {item.label && <span className="tag-red flex-shrink-0">{item.label}</span>}
                  {item.url && (
                    <a href={item.url} target="_blank" rel="noopener noreferrer"
                      className="text-txt-muted hover:text-brand-400 transition-colors opacity-0 group-hover:opacity-100">↗</a>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      ) : !error ? (
        <div className="card p-16 text-center">
          <p className="text-5xl mb-4">📡</p>
          <p className="text-txt-secondary">选择平台查看实时热搜</p>
        </div>
      ) : null}
    </div>
  );
}
