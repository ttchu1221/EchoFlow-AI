import { useState, useEffect, useRef, useCallback, useMemo, lazy, Suspense } from 'react';
import DashboardChart, { NEON_COLORS, NEON_GRADIENTS } from './DashboardChart';

const ThreeScene = lazy(() => import('./ThreeScene'));

/* ═══════════════════════════════════════════════════
 *  模拟数据生成
 * ═══════════════════════════════════════════════════ */
function generateMockData() {
  const now = new Date();
  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
  const platforms = ['小红书', '抖音', 'B站', '微博', 'YouTube'];
  const contentTypes = ['短视频', '图文', '直播', '长文', '故事'];

  return {
    kpis: [
      { label: '总用户数', value: 287650, unit: '', icon: '👥', color: 'cyan', trend: 'up', trendValue: 12.5 },
      { label: '月活跃用户', value: 156320, unit: '', icon: '🔥', color: 'blue', trend: 'up', trendValue: 8.3 },
      { label: '日均内容量', value: 3847, unit: '条', icon: '📝', color: 'purple', trend: 'up', trendValue: 15.7 },
      { label: '平均互动率', value: 8.6, unit: '%', icon: '💬', color: 'green', trend: 'up', trendValue: 2.1 },
      { label: '转化率', value: 4.2, unit: '%', icon: '🎯', color: 'amber', trend: 'down', trendValue: 0.8 },
      { label: '留存率', value: 72.5, unit: '%', icon: '📊', color: 'pink', trend: 'up', trendValue: 3.4 },
    ],
    userGrowth: {
      months,
      data: [
        { name: '新增用户', data: [12000, 15000, 18000, 22000, 28000, 35000, 42000, 48000, 55000, 62000, 71000, 82000] },
        { name: '活跃用户', data: [8000, 10000, 13000, 16000, 20000, 25000, 30000, 35000, 40000, 46000, 53000, 61000] },
        { name: '付费用户', data: [1200, 1800, 2500, 3200, 4000, 5200, 6500, 8000, 9800, 11500, 13500, 16000] },
      ],
    },
    platformDistribution: [
      { name: '小红书', value: 35 },
      { name: '抖音', value: 28 },
      { name: 'B站', value: 18 },
      { name: '微博', value: 12 },
      { name: 'YouTube', value: 7 },
    ],
    contentPerformance: {
      categories: contentTypes,
      views: [125000, 98000, 76000, 45000, 32000],
      likes: [18000, 14000, 11000, 6500, 4800],
      shares: [3200, 2800, 1900, 1200, 800],
    },
    engagementRadar: {
      indicators: [
        { name: '点赞率', max: 100 },
        { name: '评论率', max: 100 },
        { name: '分享率', max: 100 },
        { name: '收藏率', max: 100 },
        { name: '完播率', max: 100 },
        { name: '关注率', max: 100 },
      ],
      values: [85, 72, 65, 78, 88, 60],
    },
    realtimeData: Array.from({ length: 24 }, (_, i) => ({
      hour: `${i}:00`,
      active: Math.floor(Math.random() * 5000 + 2000),
      content: Math.floor(Math.random() * 200 + 50),
    })),
    funnel: [
      { name: '曝光', value: 1000000, color: '#22d3ee' },
      { name: '点击', value: 350000, color: '#3b82f6' },
      { name: '互动', value: 120000, color: '#a78bfa' },
      { name: '关注', value: 45000, color: '#34d399' },
      { name: '付费', value: 16000, color: '#fbbf24' },
    ],
    activityFeed: [
      { time: '刚刚', text: '用户 @创作者小王 发布了新短视频', icon: '🎬', color: 'cyan' },
      { time: '2分钟前', text: '话题 #AI创作 登上热搜 TOP3', icon: '🔥', color: 'red' },
      { time: '5分钟前', text: '平台互动量突破 10万/小时', icon: '🚀', color: 'green' },
      { time: '8分钟前', text: '新增付费用户 127 人', icon: '💰', color: 'amber' },
      { time: '12分钟前', text: '内容审核通过率 98.5%', icon: '✅', color: 'blue' },
      { time: '15分钟前', text: '系统自动扩容完成，QPS 提升 40%', icon: '⚡', color: 'purple' },
      { time: '20分钟前', text: 'B站平台数据同步完成', icon: '📡', color: 'cyan' },
      { time: '25分钟前', text: '新增创作者 56 人', icon: '✨', color: 'pink' },
    ],
    topContent: [
      { rank: 1, title: 'AI 一键生成爆款标题，效率提升10倍', platform: '小红书', heat: 98500, trend: 'up' },
      { rank: 2, title: '30天涨粉1万的秘诀分享', platform: '抖音', heat: 87200, trend: 'up' },
      { rank: 3, title: '2026年最值得关注的AI工具', platform: 'B站', heat: 76800, trend: 'up' },
      { rank: 4, title: '新手博主必看的内容创作指南', platform: '微博', heat: 65400, trend: 'down' },
      { rank: 5, title: '从0到10万粉的完整攻略', platform: 'YouTube', heat: 54100, trend: 'up' },
    ],
  };
}

/* ═══════════════════════════════════════════════════
 *  计数动画 Hook
 * ═══════════════════════════════════════════════════ */
function useCountUp(target, duration = 1500) {
  const [value, setValue] = useState(0);
  const rafRef = useRef(null);

  useEffect(() => {
    const start = performance.now();
    const animate = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(target * eased * 100) / 100);
      if (progress < 1) rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [target, duration]);

  return value;
}

/* ═══════════════════════════════════════════════════
 *  数字翻牌器组件
 * ═══════════════════════════════════════════════════ */
function FlipNumber({ value, color = 'cyan' }) {
  const display = useCountUp(value);
  const formatted = display >= 10000
    ? (display / 10000).toFixed(1) + '万'
    : display >= 1000
    ? display.toLocaleString()
    : Number.isInteger(display) ? display.toString() : display.toFixed(1);

  const colorMap = {
    cyan: 'text-brand-400',
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    green: 'text-emerald-400',
    amber: 'text-amber-400',
    pink: 'text-pink-400',
    red: 'text-red-400',
  };

  return (
    <span className={`text-2xl sm:text-3xl font-bold ${colorMap[color] || colorMap.cyan} tracking-tight dashboard-glow-text`}>
      {formatted}
    </span>
  );
}

/* ═══════════════════════════════════════════════════
 *  KPI 卡片组件
 * ═══════════════════════════════════════════════════ */
function DashKpiCard({ label, value, unit, icon, color, trend, trendValue }) {
  const colorMap = {
    cyan:   { border: 'border-brand-500/30', bg: 'bg-brand-500/8',  glow: 'shadow-neon-cyan',  icon: 'text-brand-400' },
    blue:   { border: 'border-blue-500/30',   bg: 'bg-blue-500/8',   glow: 'shadow-neon-blue',  icon: 'text-blue-400' },
    purple: { border: 'border-purple-500/30', bg: 'bg-purple-500/8', glow: 'shadow-neon-purple',icon: 'text-purple-400' },
    green:  { border: 'border-emerald-500/30',bg: 'bg-emerald-500/8',glow: 'shadow-neon-green', icon: 'text-emerald-400' },
    amber:  { border: 'border-amber-500/30',  bg: 'bg-amber-500/8',  glow: 'shadow-neon-amber', icon: 'text-amber-400' },
    pink:   { border: 'border-pink-500/30',   bg: 'bg-pink-500/8',   glow: 'shadow-neon-pink',  icon: 'text-pink-400' },
  };
  const c = colorMap[color] || colorMap.cyan;

  return (
    <div className={`relative overflow-hidden rounded-xl border ${c.border} ${c.bg} p-3 sm:p-4 transition-all duration-300 hover:scale-[1.03] backdrop-blur-sm dashboard-kpi-card`}>
      <div className={`absolute -top-6 -right-6 w-20 h-20 rounded-full ${c.bg} blur-2xl opacity-50`} />
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] sm:text-xs font-medium text-txt-secondary uppercase tracking-wider">{label}</span>
          <span className={`text-base sm:text-lg ${c.icon}`}>{icon}</span>
        </div>
        <div className="flex items-baseline gap-1">
          <FlipNumber value={value} color={color} />
          {unit && <span className="text-xs text-txt-muted">{unit}</span>}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 mt-1.5 text-[10px] sm:text-xs ${trend === 'up' ? 'text-emerald-400' : 'text-red-400'}`}>
            <span>{trend === 'up' ? '↑' : '↓'}</span>
            <span>{trendValue}%</span>
            <span className="text-txt-muted ml-0.5">vs 上期</span>
          </div>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
 *  实时活动流组件
 * ═══════════════════════════════════════════════════ */
function ActivityFeed({ items }) {
  const [visibleCount, setVisibleCount] = useState(4);

  useEffect(() => {
    const timer = setInterval(() => {
      setVisibleCount(prev => (prev >= items.length ? 4 : prev + 1));
    }, 3000);
    return () => clearInterval(timer);
  }, [items.length]);

  const colorMap = {
    cyan: 'border-brand-500/40 text-brand-400',
    red: 'border-red-500/40 text-red-400',
    green: 'border-emerald-500/40 text-emerald-400',
    amber: 'border-amber-500/40 text-amber-400',
    blue: 'border-blue-500/40 text-blue-400',
    purple: 'border-purple-500/40 text-purple-400',
    pink: 'border-pink-500/40 text-pink-400',
  };

  return (
    <div className="space-y-2 overflow-hidden">
      {items.slice(0, visibleCount).map((item, i) => (
        <div
          key={i}
          className={`flex items-center gap-2.5 p-2.5 rounded-lg bg-panel-100/40 border-l-2 ${colorMap[item.color] || colorMap.cyan} animate-slide-in-left transition-all duration-300`}
          style={{ animationDelay: `${i * 100}ms` }}
        >
          <span className="text-sm flex-shrink-0">{item.icon}</span>
          <span className="text-xs text-txt-secondary flex-1 truncate">{item.text}</span>
          <span className="text-[10px] text-txt-muted flex-shrink-0">{item.time}</span>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
 *  TOP 内容排行组件
 * ═══════════════════════════════════════════════════ */
function TopContentTable({ items }) {
  return (
    <div className="space-y-1.5">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-panel-100/40 transition-colors group">
          <span className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold flex-shrink-0 ${
            i === 0 ? 'bg-gradient-to-br from-amber-400 to-amber-600 text-white' :
            i === 1 ? 'bg-gradient-to-br from-slate-300 to-slate-500 text-white' :
            i === 2 ? 'bg-gradient-to-br from-amber-600 to-amber-800 text-white' :
            'bg-panel-100 text-txt-muted'
          }`}>{item.rank}</span>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-txt-primary truncate">{item.title}</p>
            <span className="text-[10px] text-txt-muted">{item.platform}</span>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            <span className="text-[10px]">🔥</span>
            <span className="text-xs font-mono text-neon-amber">
              {item.heat > 10000 ? (item.heat / 10000).toFixed(1) + '万' : item.heat.toLocaleString()}
            </span>
          </div>
          <span className={`text-xs ${item.trend === 'up' ? 'text-emerald-400' : 'text-red-400'}`}>
            {item.trend === 'up' ? '↑' : '↓'}
          </span>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
 *  面板标题组件
 * ═══════════════════════════════════════════════════ */
function PanelTitle({ title, color = 'cyan' }) {
  const colorMap = {
    cyan: 'from-brand-400 to-brand-600',
    blue: 'from-blue-400 to-blue-600',
    purple: 'from-purple-400 to-purple-600',
    green: 'from-emerald-400 to-emerald-600',
    amber: 'from-amber-400 to-amber-600',
    pink: 'from-pink-400 to-pink-600',
  };

  return (
    <h3 className="text-sm font-semibold text-txt-primary mb-3 flex items-center gap-2">
      <span className={`w-1 h-4 rounded-full bg-gradient-to-b ${colorMap[color] || colorMap.cyan}`} />
      {title}
    </h3>
  );
}

/* ═══════════════════════════════════════════════════
 *  主面板卡片
 * ═══════════════════════════════════════════════════ */
function DashCard({ children, className = '', glow = false }) {
  return (
    <div className={`${glow ? 'card-glow' : 'card'} p-4 dashboard-panel ${className}`}>
      {children}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
 *  主页面
 * ═══════════════════════════════════════════════════ */

const EMPTY_DATA = {
  kpis: [],
  userGrowth: { months: [], data: [] },
  platformDistribution: [],
  contentPerformance: { categories: [], views: [], likes: [], shares: [] },
  engagementRadar: { indicators: [], values: [] },
  realtimeData: [],
  funnel: [],
  activityFeed: [],
  topContent: [],
};

async function fetchDashboardData() {
  const res = await fetch('/api/dashboard');
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export default function DashboardPage() {
  const [data, setData] = useState(EMPTY_DATA);
  const [loading, setLoading] = useState(true);
  const [time, setTime] = useState(new Date());
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  /* 拉取真实数据 */
  useEffect(() => {
    let cancelled = false;
    fetchDashboardData()
      .then(d => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  /* 定时刷新（30 秒） */
  useEffect(() => {
    const timer = setInterval(() => {
      fetchDashboardData().then(setData).catch(() => {});
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  /* 全屏切换 */
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  /* 时钟 */
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  /* ── 图表配置 ──────────────────────────────── */

  /* 用户增长趋势 - 面积图 */
  const userGrowthOption = useMemo(() => ({
    grid: { left: 50, right: 20, top: 30, bottom: 30 },
    legend: {
      data: data.userGrowth.data.map(d => d.name),
      textStyle: { color: '#94a3b8', fontSize: 10 },
      top: 0, right: 0,
    },
    xAxis: {
      type: 'category',
      data: data.userGrowth.months,
      axisLabel: { color: '#64748b', fontSize: 10 },
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#64748b', fontSize: 10, formatter: (v) => v >= 10000 ? (v / 10000) + '万' : v },
      splitLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.2)', type: 'dashed' } },
    },
    series: data.userGrowth.data.map((d, i) => ({
      name: d.name,
      type: 'line',
      data: d.data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: { width: 2, color: ['#22d3ee', '#3b82f6', '#a78bfa'][i] },
      itemStyle: { color: ['#22d3ee', '#3b82f6', '#a78bfa'][i] },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: ['#22d3ee', '#3b82f6', '#a78bfa'][i] + '30' },
            { offset: 1, color: ['#22d3ee', '#3b82f6', '#a78bfa'][i] + '05' },
          ],
        },
      },
    })),
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross', lineStyle: { color: 'rgba(34, 211, 238, 0.3)' } } },
    animationDuration: 1200,
    animationEasing: 'cubicOut',
  }), [data.userGrowth]);

  /* 平台分布 - 环形图 */
  const platformPieOption = useMemo(() => ({
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '50%'],
      data: data.platformDistribution.map((d, i) => ({
        ...d,
        itemStyle: { color: NEON_COLORS[i] },
      })),
      label: {
        show: true,
        color: '#94a3b8',
        fontSize: 10,
        fontFamily: '"PingFang SC", "Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif',
        formatter: '{b}\n{d}%',
      },
      emphasis: {
        label: { fontSize: 13, fontWeight: 'bold', color: '#e2e8f0' },
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(34, 211, 238, 0.3)' },
      },
      itemStyle: { borderColor: '#0d1117', borderWidth: 3 },
    }],
    tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)' },
    animationDuration: 1000,
  }), [data.platformDistribution]);

  /* 内容表现 - 柱状图 */
  const contentBarOption = useMemo(() => ({
    grid: { left: 50, right: 20, top: 30, bottom: 30 },
    legend: {
      data: ['播放量', '点赞数', '分享数'],
      textStyle: { color: '#94a3b8', fontSize: 10 },
      top: 0, right: 0,
    },
    xAxis: {
      type: 'category',
      data: data.contentPerformance.categories,
      axisLabel: { color: '#64748b', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#64748b', fontSize: 10, formatter: (v) => v >= 10000 ? (v / 10000) + '万' : v },
      splitLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.2)', type: 'dashed' } },
    },
    series: [
      { name: '播放量', type: 'bar', data: data.contentPerformance.views, barWidth: 12, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#22d3ee' }, { offset: 1, color: '#0891b2' }] }, borderRadius: [4, 4, 0, 0] } },
      { name: '点赞数', type: 'bar', data: data.contentPerformance.likes, barWidth: 12, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#3b82f6' }, { offset: 1, color: '#1d4ed8' }] }, borderRadius: [4, 4, 0, 0] } },
      { name: '分享数', type: 'bar', data: data.contentPerformance.shares, barWidth: 12, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#a78bfa' }, { offset: 1, color: '#7c3aed' }] }, borderRadius: [4, 4, 0, 0] } },
    ],
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    animationDuration: 1000,
  }), [data.contentPerformance]);

  /* 互动雷达图 */
  const radarOption = useMemo(() => ({
    radar: {
      indicator: data.engagementRadar.indicators,
      shape: 'polygon',
      axisName: { color: '#94a3b8', fontSize: 10 },
      splitArea: { areaStyle: { color: ['rgba(34,211,238,0.02)', 'rgba(34,211,238,0.04)'] } },
      splitLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.4)' } },
      axisLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.4)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: data.engagementRadar.values,
        name: '互动指标',
        areaStyle: { color: 'rgba(34, 211, 238, 0.15)' },
        lineStyle: { color: '#22d3ee', width: 2 },
        itemStyle: { color: '#22d3ee' },
      }, {
        value: data.engagementRadar.values.map(v => v * 0.85),
        name: '上期',
        areaStyle: { color: 'rgba(167, 139, 250, 0.08)' },
        lineStyle: { color: '#a78bfa', width: 1, type: 'dashed' },
        itemStyle: { color: '#a78bfa' },
      }],
    }],
    legend: {
      data: ['互动指标', '上期'],
      textStyle: { color: '#94a3b8', fontSize: 10 },
      bottom: 0,
    },
    tooltip: { trigger: 'item' },
    animationDuration: 1200,
  }), [data.engagementRadar]);

  /* 24小时活跃曲线 */
  const realtimeLineOption = useMemo(() => ({
    grid: { left: 40, right: 10, top: 10, bottom: 25 },
    xAxis: {
      type: 'category',
      data: data.realtimeData.map(d => d.hour),
      axisLabel: { color: '#64748b', fontSize: 9, interval: 3 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#64748b', fontSize: 9 },
      splitLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.15)', type: 'dashed' } },
    },
    series: [{
      type: 'line',
      data: data.realtimeData.map(d => d.active),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#22d3ee', width: 2 },
      areaStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(34,211,238,0.25)' }, { offset: 1, color: 'rgba(34,211,238,0.02)' }] },
      },
    }, {
      type: 'line',
      data: data.realtimeData.map(d => d.content * 10),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#a78bfa', width: 1.5 },
      areaStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(167,139,250,0.15)' }, { offset: 1, color: 'rgba(167,139,250,0.02)' }] },
      },
    }],
    tooltip: { trigger: 'axis' },
    animationDuration: 1500,
  }), [data.realtimeData]);

  /* 转化漏斗 - 横向条形图 */
  const funnelOption = useMemo(() => ({
    grid: { left: 60, right: 40, top: 10, bottom: 10 },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category',
      data: data.funnel.map(f => f.name).reverse(),
      axisLabel: { color: '#94a3b8', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: data.funnel.map((f, i) => ({
        value: f.value,
        itemStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: f.color + '22' }, { offset: 1, color: f.color }] },
          borderRadius: [0, 6, 6, 0],
        },
      })).reverse(),
      barWidth: 18,
      label: {
        show: true, position: 'right',
        color: '#e2e8f0', fontSize: 11,
        formatter: (p) => p.value >= 10000 ? (p.value / 10000).toFixed(1) + '万' : p.value.toLocaleString(),
      },
    }],
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    animationDuration: 1200,
    animationDelay: (idx) => idx * 200,
  }), [data.funnel]);

  const formatTime = (d) => {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };
  const formatDate = (d) => {
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' });
  };

  return (
    <div ref={containerRef} className="relative w-full min-h-screen bg-panel dashboard-container overflow-auto">
      {/* ── 加载状态 ──────────────────────────────── */}
      {loading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-panel/80 backdrop-blur-sm">
          <div className="text-center">
            <div className="inline-block w-10 h-10 border-4 border-brand-500/30 border-t-brand-400 rounded-full animate-spin mb-4" />
            <p className="text-txt-secondary text-sm">正在加载真实数据...</p>
          </div>
        </div>
      )}

      {/* ── 3D 背景场景 ───────────────────────────── */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <Suspense fallback={null}>
          <ThreeScene className="w-full h-full" />
        </Suspense>
      </div>

      {/* ── 扫描线叠加 ────────────────────────────── */}
      <div className="fixed inset-0 z-[1] pointer-events-none scanline opacity-30" />

      {/* ── 主内容 ────────────────────────────────── */}
      <div className="relative z-10 flex flex-col min-h-screen">
        {/* ── 顶部标题栏 ────────────────────────────── */}
        <header className="sticky top-0 z-20 backdrop-blur-xl bg-panel/70 border-b border-panel-border">
          <div className="max-w-[1920px] mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold text-sm shadow-neon-cyan">
                E
              </div>
              <div>
                <h1 className="text-base sm:text-lg font-bold text-txt-bright tracking-tight">
                  EchoFlow <span className="text-brand-400">数据驾驶舱</span>
                </h1>
                <p className="text-[10px] sm:text-xs text-txt-muted">智能内容增长运营系统 · 全局数据监控</p>
              </div>
            </div>

            <div className="flex items-center gap-3 sm:gap-4">
              {/* 实时时钟 */}
              <div className="hidden sm:flex flex-col items-end">
                <span className="text-sm font-mono text-brand-400 dashboard-glow-text">{formatTime(time)}</span>
                <span className="text-[10px] text-txt-muted">{formatDate(time)}</span>
              </div>

              {/* 系统状态 */}
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-panel-100 border border-panel-border">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
                </span>
                <span className="text-[10px] text-txt-secondary">系统正常</span>
              </div>

              {/* 全屏按钮 */}
              <button
                onClick={toggleFullscreen}
                className="p-2 rounded-lg text-txt-muted hover:text-brand-400 hover:bg-panel-100 transition-colors"
                title={isFullscreen ? '退出全屏' : '全屏展示'}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {isFullscreen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  )}
                </svg>
              </button>
            </div>
          </div>
        </header>

        {/* ── 大屏内容区 ────────────────────────────── */}
        <main className="flex-1 max-w-[1920px] mx-auto w-full px-3 sm:px-6 py-4 sm:py-6 space-y-4 sm:space-y-5">

          {/* ── KPI 卡片行 ───────────────────────────── */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3">
            {data.kpis.map((kpi, i) => (
              <DashKpiCard key={i} {...kpi} />
            ))}
          </div>

          {/* ── 第一行图表 ───────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4">
            {/* 用户增长趋势 - 占2列 */}
            <div className="lg:col-span-2">
              <DashCard>
                <PanelTitle title="用户增长趋势" color="cyan" />
                <DashboardChart option={userGrowthOption} height={280} />
              </DashCard>
            </div>

            {/* 平台分布 */}
            <DashCard>
              <PanelTitle title="平台分布" color="purple" />
              <DashboardChart option={platformPieOption} height={220} />
              <div className="mt-2 space-y-1">
                {data.platformDistribution.map((p, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: NEON_COLORS[i] }} />
                    <span className="text-txt-secondary flex-1">{p.name}</span>
                    <span className="font-mono text-txt-primary">{p.value}%</span>
                  </div>
                ))}
              </div>
            </DashCard>
          </div>

          {/* ── 第二行图表 ───────────────────────────── */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {/* 内容表现 - 占2列 */}
            <div className="md:col-span-2">
              <DashCard>
                <PanelTitle title="内容表现对比" color="blue" />
                <DashboardChart option={contentBarOption} height={260} />
              </DashCard>
            </div>

            {/* 互动雷达图 */}
            <DashCard>
              <PanelTitle title="互动指标雷达" color="green" />
              <DashboardChart option={radarOption} height={260} />
            </DashCard>

            {/* 转化漏斗 */}
            <DashCard>
              <PanelTitle title="转化漏斗" color="amber" />
              <DashboardChart option={funnelOption} height={260} />
            </DashCard>
          </div>

          {/* ── 第三行 ──────────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4">
            {/* 24小时活跃曲线 */}
            <DashCard>
              <PanelTitle title="24小时活跃趋势" color="cyan" />
              <DashboardChart option={realtimeLineOption} height={200} />
              <div className="flex items-center gap-4 mt-2">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 rounded bg-brand-400" />
                  <span className="text-[10px] text-txt-muted">活跃用户</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 rounded bg-purple-400" />
                  <span className="text-[10px] text-txt-muted">内容发布</span>
                </div>
              </div>
            </DashCard>

            {/* TOP 内容排行 */}
            <DashCard>
              <PanelTitle title="🔥 热门内容排行" color="red" />
              <TopContentTable items={data.topContent} />
            </DashCard>

            {/* 实时活动流 */}
            <DashCard>
              <PanelTitle title="📡 实时动态" color="purple" />
              <ActivityFeed items={data.activityFeed} />
            </DashCard>
          </div>

          {/* ── 底部装饰条 ────────────────────────────── */}
          <div className="flex items-center justify-center gap-3 py-4">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-brand-500/30 to-transparent" />
            <span className="text-[10px] text-txt-muted tracking-widest uppercase">EchoFlow AI · Data Visualization</span>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-brand-500/30 to-transparent" />
          </div>
        </main>
      </div>
    </div>
  );
}
