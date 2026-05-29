import { useState, useEffect } from 'react';
import { getHotSearch } from '../api/client';

const PLATFORMS = [
  { id: 'bilibili',    label: 'B站',  color: 'from-blue-400 to-blue-600',  bg: 'bg-blue-50',   text: 'text-blue-600'  },
  { id: 'douyin',      label: '抖音', color: 'from-gray-700 to-gray-900',  bg: 'bg-gray-50',   text: 'text-gray-600'  },
  { id: 'xiaohongshu', label: '小红书', color: 'from-red-400 to-red-600',  bg: 'bg-red-50',    text: 'text-red-600'   },
  { id: 'weibo',       label: '微博', color: 'from-orange-400 to-red-500', bg: 'bg-orange-50', text: 'text-orange-600'},
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

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">实时热搜</h2>
          <p className="text-sm text-gray-500 mt-1">聚合多平台热榜数据，实时追踪内容趋势</p>
        </div>
        {lastUpdate && (
          <span className="text-xs text-gray-400">更新于 {lastUpdate}</span>
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
                ? `bg-gradient-to-r ${p.color} text-white shadow-md`
                : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300 hover:shadow-sm'
              }
            `}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* 内容区 */}
      {error && (
        <div className="card p-4 border-red-200 bg-red-50">
          <p className="text-sm text-red-600">⚠️ {error}</p>
          <p className="text-xs text-red-400 mt-1">请确保后端已启动，且网络可访问聚合数据源</p>
        </div>
      )}

      {loading ? (
        <div className="grid gap-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="card-flat p-4 flex items-center gap-4">
              <div className="shimmer w-8 h-8" />
              <div className="shimmer h-4 flex-1" />
              <div className="shimmer w-16 h-4" />
            </div>
          ))}
        </div>
      ) : items.length > 0 ? (
        <div className="card divide-y divide-gray-50">
          {items.map((item, i) => (
            <div key={i} className="flex items-center gap-4 px-5 py-3.5 hover:bg-gray-50/60 transition-colors group">
              {/* 排名 */}
              <div className={`
                w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0
                ${i < 3
                  ? 'bg-gradient-to-br ' + currentPlatform.color + ' text-white'
                  : 'bg-gray-100 text-gray-500'
                }
              `}>
                {i + 1}
              </div>

              {/* 关键词 */}
              <div className="flex-1 min-w-0">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-gray-800 hover:text-brand-600 transition-colors truncate block"
                >
                  {item.keyword}
                </a>
              </div>

              {/* 热度 */}
              {item.heat_score > 0 && (
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span className="text-xs">🔥</span>
                  <span className="text-xs font-medium text-gray-500">
                    {item.heat_score > 10000
                      ? (item.heat_score / 10000).toFixed(1) + '万'
                      : item.heat_score.toLocaleString()
                    }
                  </span>
                </div>
              )}

              {/* 标签 */}
              {item.label && (
                <span className="tag-red flex-shrink-0">{item.label}</span>
              )}

              {/* 外链 */}
              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-300 hover:text-brand-500 transition-colors opacity-0 group-hover:opacity-100 flex-shrink-0"
                >
                  ↗
                </a>
              )}
            </div>
          ))}
        </div>
      ) : !error ? (
        <div className="card p-12 text-center">
          <p className="text-4xl mb-3">📡</p>
          <p className="text-sm text-gray-400">选择平台查看实时热搜</p>
        </div>
      ) : null}
    </div>
  );
}
