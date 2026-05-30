/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        /* 主品牌色 — 科技青 */
        brand: {
          50:  '#ecfeff',
          100: '#cffafe',
          200: '#a5f3fc',
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
          950: '#083344',
        },
        /* 深色面板 */
        panel: {
          DEFAULT: '#0d1117',
          50:  '#161b22',
          100: '#1c2333',
          200: '#21293a',
          300: '#2d3548',
          400: '#384256',
          border: 'rgba(56, 66, 86, 0.6)',
        },
        /* 霓虹辅色 */
        neon: {
          cyan:   '#22d3ee',
          blue:   '#3b82f6',
          purple: '#a78bfa',
          pink:   '#f472b6',
          green:  '#34d399',
          amber:  '#fbbf24',
          red:    '#f87171',
        },
        /* 文字 */
        txt: {
          primary:   '#e2e8f0',
          secondary: '#94a3b8',
          muted:     '#64748b',
          bright:    '#f1f5f9',
        },
      },
      fontFamily: {
        sans: ['"Inter"', '"PingFang SC"', '"Noto Sans SC"', '"Microsoft YaHei"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      boxShadow: {
        'neon-cyan':   '0 0 15px rgba(34, 211, 238, 0.25), 0 0 40px rgba(34, 211, 238, 0.1)',
        'neon-blue':   '0 0 15px rgba(59, 130, 246, 0.25), 0 0 40px rgba(59, 130, 246, 0.1)',
        'neon-purple': '0 0 15px rgba(167, 139, 250, 0.25), 0 0 40px rgba(167, 139, 250, 0.1)',
        'neon-green':  '0 0 15px rgba(52, 211, 153, 0.25), 0 0 40px rgba(52, 211, 153, 0.1)',
        'neon-amber':  '0 0 15px rgba(251, 191, 36, 0.25), 0 0 40px rgba(251, 191, 36, 0.1)',
        'neon-red':    '0 0 15px rgba(248, 113, 113, 0.25), 0 0 40px rgba(248, 113, 113, 0.1)',
        'neon-pink':   '0 0 15px rgba(244, 114, 182, 0.25), 0 0 40px rgba(244, 114, 182, 0.1)',
        'panel':       '0 4px 24px rgba(0, 0, 0, 0.3)',
        'glow':        '0 0 30px rgba(34, 211, 238, 0.15)',
      },
      borderRadius: {
        'xl': '0.875rem',
        '2xl': '1rem',
        '3xl': '1.25rem',
      },
      animation: {
        'fade-in':       'fadeIn 0.4s ease-out',
        'slide-up':      'slideUp 0.4s ease-out',
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'pulse-soft':    'pulseSoft 2s ease-in-out infinite',
        'glow-pulse':    'glowPulse 2s ease-in-out infinite',
        'border-flow':   'borderFlow 3s linear infinite',
        'count-up':      'countUp 1s ease-out',
        'float':         'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:      { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp:     { '0%': { opacity: '0', transform: 'translateY(16px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        slideInLeft: { '0%': { opacity: '0', transform: 'translateX(-16px)' }, '100%': { opacity: '1', transform: 'translateX(0)' } },
        pulseSoft:   { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0.6' } },
        glowPulse:   { '0%, 100%': { boxShadow: '0 0 15px rgba(34, 211, 238, 0.2)' }, '50%': { boxShadow: '0 0 30px rgba(34, 211, 238, 0.4)' } },
        borderFlow:  { '0%': { backgroundPosition: '0% 50%' }, '50%': { backgroundPosition: '100% 50%' }, '100%': { backgroundPosition: '0% 50%' } },
        countUp:     { '0%': { opacity: '0', transform: 'translateY(10px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        float:       { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-8px)' } },
      },
    },
  },
  plugins: [],
}
