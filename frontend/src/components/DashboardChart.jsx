import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { BarChart, LineChart, PieChart, RadarChart, GaugeChart, FunnelChart, ScatterChart } from 'echarts/charts';
import {
  TitleComponent, TooltipComponent, GridComponent, LegendComponent,
  DataZoomComponent, ToolboxComponent, MarkLineComponent, MarkPointComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  BarChart, LineChart, PieChart, RadarChart, GaugeChart, FunnelChart, ScatterChart,
  TitleComponent, TooltipComponent, GridComponent, LegendComponent,
  DataZoomComponent, ToolboxComponent, MarkLineComponent, MarkPointComponent,
  CanvasRenderer,
]);

/* ── 全局深色主题 ────────────────────────────────── */
echarts.registerTheme('echowflow', {
  backgroundColor: 'transparent',
  textStyle: { color: '#94a3b8', fontFamily: '"Inter", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif' },
  title: { textStyle: { color: '#e2e8f0' }, subtextStyle: { color: '#64748b' } },
  legend: { textStyle: { color: '#94a3b8' } },
  tooltip: {
    backgroundColor: 'rgba(13, 17, 23, 0.95)',
    borderColor: 'rgba(34, 211, 238, 0.2)',
    textStyle: { color: '#e2e8f0' },
    extraCssText: 'backdrop-filter: blur(12px); border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);',
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.6)' } },
    axisTick: { lineStyle: { color: 'rgba(56, 66, 86, 0.6)' } },
    axisLabel: { color: '#64748b' },
    splitLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.3)' } },
  },
  valueAxis: {
    axisLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.6)' } },
    axisTick: { lineStyle: { color: 'rgba(56, 66, 86, 0.6)' } },
    axisLabel: { color: '#64748b' },
    splitLine: { lineStyle: { color: 'rgba(56, 66, 86, 0.2)', type: 'dashed' } },
  },
});

/**
 * 通用仪表盘图表组件
 * @param {object} props
 * @param {object} props.option - ECharts option
 * @param {number|string} [props.height=300] - 图表高度
 * @param {string} [props.title] - 标题
 * @param {string} [props.subtitle] - 副标题
 * @param {string} [props.className] - 额外类名
 */
export default function DashboardChart({ option, height = 300, title, subtitle, className = '' }) {
  const mergedOption = {
    animation: true,
    animationDuration: 800,
    animationEasing: 'cubicOut',
    ...option,
    ...(title ? { title: { text: title, subtext: subtitle, left: 'center', top: 8, textStyle: { fontSize: 14, fontWeight: 600, color: '#e2e8f0' }, subtextStyle: { fontSize: 12, color: '#64748b' }, ...option.title } } : {}),
  };

  return (
    <div className={className}>
      <ReactEChartsCore
        echarts={echarts}
        option={mergedOption}
        theme="echowflow"
        style={{ height: typeof height === 'number' ? `${height}px` : height, width: '100%' }}
        opts={{ renderer: 'canvas' }}
        notMerge
      />
    </div>
  );
}

/* ── 色板常量（供各面板使用）─────────────────────────── */
export const NEON_COLORS = [
  '#22d3ee', // cyan
  '#3b82f6', // blue
  '#a78bfa', // purple
  '#f472b6', // pink
  '#34d399', // green
  '#fbbf24', // amber
  '#f87171', // red
  '#818cf8', // indigo
  '#2dd4bf', // teal
  '#fb923c', // orange
];

export const NEON_GRADIENTS = {
  cyan:   ['#22d3ee', '#0891b2'],
  blue:   ['#3b82f6', '#1d4ed8'],
  purple: ['#a78bfa', '#7c3aed'],
  pink:   ['#f472b6', '#db2777'],
  green:  ['#34d399', '#059669'],
  amber:  ['#fbbf24', '#d97706'],
  red:    ['#f87171', '#dc2626'],
};
