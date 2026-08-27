import { useEffect, useRef, useState } from 'react';

const COLOR_MAP = {
  cyan:   { bg: 'bg-brand-500/10', border: 'border-brand-500/20', text: 'text-brand-400', glow: 'shadow-neon-cyan', icon: 'text-brand-400' },
  blue:   { bg: 'bg-blue-500/10',  border: 'border-blue-500/20',  text: 'text-blue-400',  glow: 'shadow-neon-blue', icon: 'text-blue-400' },
  purple: { bg: 'bg-purple-500/10',border: 'border-purple-500/20',text: 'text-purple-400',glow: 'shadow-neon-purple',icon:'text-purple-400' },
  green:  { bg: 'bg-emerald-500/10',border:'border-emerald-500/20',text:'text-emerald-400',glow:'shadow-neon-green',icon:'text-emerald-400' },
  amber:  { bg: 'bg-amber-500/10',border: 'border-amber-500/20', text: 'text-amber-400', glow: 'shadow-neon-amber', icon: 'text-amber-400' },
  red:    { bg: 'bg-red-500/10',   border: 'border-red-500/20',   text: 'text-red-400',   glow: 'shadow-neon-red',  icon: 'text-red-400' },
  pink:   { bg: 'bg-pink-500/10',  border: 'border-pink-500/20',  text: 'text-pink-400',  glow: 'shadow-neon-pink', icon: 'text-pink-400' },
};

/**
 * 霓虹风格 KPI 统计卡片
 * @param {object} props
 * @param {string} props.label - 指标名称
 * @param {number|string} props.value - 指标值
 * @param {string} [props.unit] - 单位
 * @param {string} [props.icon] - 图标 emoji
 * @param {string} [props.color='cyan'] - 颜色主题
 * @param {string} [props.trend] - 趋势方向 'up'|'down'
 * @param {number} [props.trendValue] - 趋势值
 * @param {string} [props.className] - 额外类名
 */
export default function StatsCard({ label, value, unit, icon, color = 'cyan', trend, trendValue, className = '' }) {
  const c = COLOR_MAP[color] || COLOR_MAP.cyan;
  const [displayValue, setDisplayValue] = useState(0);
  const rafRef = useRef(null);
  const numValue = typeof value === 'number' ? value : parseFloat(value) || 0;

  useEffect(() => {
    const duration = 1000;
    const startTime = performance.now();
    const startVal = 0;

    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.round(startVal + (numValue - startVal) * eased * 100) / 100);
      if (progress < 1) rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [numValue]);

  const formatValue = (v) => {
    if (typeof value === 'string' && isNaN(parseFloat(value))) return value;
    if (v >= 10000) return (v / 10000).toFixed(1) + '万';
    if (v >= 1000) return v.toLocaleString();
    if (Number.isInteger(v)) return v.toString();
    return v.toFixed(1);
  };

  return (
    <div className={`relative overflow-hidden rounded-2xl border ${c.border} ${c.bg} p-5 transition-all duration-300 hover:scale-[1.02] ${className}`}>
      {/* 背景光晕 */}
      <div className={`absolute -top-8 -right-8 w-24 h-24 rounded-full ${c.bg} blur-2xl opacity-60`} />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-txt-secondary uppercase tracking-wider">{label}</span>
          {icon && <span className={`text-lg ${c.icon}`}>{icon}</span>}
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className={`text-3xl font-bold ${c.text} tracking-tight`} style={{ textShadow: `0 0 20px ${c.text === 'text-brand-400' ? 'rgba(34,211,238,0.3)' : 'rgba(100,116,139,0.2)'}` }}>
            {formatValue(displayValue)}
          </span>
          {unit && <span className="text-sm text-txt-muted">{unit}</span>}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 mt-2 text-xs ${trend === 'up' ? 'text-emerald-400' : 'text-red-400'}`}>
            <span>{trend === 'up' ? '↑' : '↓'}</span>
            {trendValue !== undefined && <span>{trendValue}%</span>}
            <span className="text-txt-muted ml-1">vs 上期</span>
          </div>
        )}
      </div>
    </div>
  );
}
