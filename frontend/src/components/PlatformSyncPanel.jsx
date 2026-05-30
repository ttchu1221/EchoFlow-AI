import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api/platform';

function formatNumber(num) {
  if (!num && num !== 0) return '0';
  num = Number(num) || 0;
  if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
  if (num >= 10000) return (num / 10000).toFixed(1) + '万';
  return num.toLocaleString();
}

export default function PlatformSyncPanel() {
  const [collected, setCollected] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

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

  return (
    <div style={{ padding: 24 }}>
      {/* 标题 */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>⭐ 爆款采集</h1>
        <p style={{ color: '#666', margin: '4px 0 0 0', fontSize: 14 }}>
          浏览抖音时点击右侧 ⭐ 按钮，一键采集爆款视频
        </p>
      </div>

      {/* 统计卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
        <div style={{
          padding: 20, borderRadius: 12,
          background: 'linear-gradient(135deg, #667eea, #764ba2)',
          color: '#fff', textAlign: 'center',
        }}>
          <div style={{ fontSize: 32, fontWeight: 700 }}>{total}</div>
          <div style={{ fontSize: 13, opacity: 0.8 }}>总采集</div>
        </div>
        <div style={{
          padding: 20, borderRadius: 12,
          background: 'linear-gradient(135deg, #f093fb, #f5576c)',
          color: '#fff', textAlign: 'center',
        }}>
          <div style={{ fontSize: 32, fontWeight: 700 }}>{todayCount}</div>
          <div style={{ fontSize: 13, opacity: 0.8 }}>今日采集</div>
        </div>
        <div style={{
          padding: 20, borderRadius: 12,
          background: 'linear-gradient(135deg, #4facfe, #00f2fe)',
          color: '#fff', textAlign: 'center',
        }}>
          <div style={{ fontSize: 32, fontWeight: 700 }}>
            {collected.filter(v => v.platform === 'douyin').length}
          </div>
          <div style={{ fontSize: 13, opacity: 0.8 }}>抖音</div>
        </div>
      </div>

      {/* 使用说明 */}
      <div style={{
        background: '#f0f0ff', borderRadius: 12, padding: 20, marginBottom: 24,
        fontSize: 14, lineHeight: 1.8,
      }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>📖 使用方法</h3>
        <ol style={{ paddingLeft: 20 }}>
          <li>安装浏览器插件（<code style={{ background: '#e0e0ff', padding: '2px 6px', borderRadius: 4 }}>extensions/douyin</code>）</li>
          <li>打开 <a href="https://www.douyin.com" target="_blank" rel="noopener noreferrer">douyin.com</a> 浏览视频</li>
          <li>看到爆款视频 → 点击页面右侧的 <strong>⭐</strong> 按钮</li>
          <li>视频自动保存到此处</li>
        </ol>
      </div>

      {/* 采集列表 */}
      <div style={{
        background: '#fff', borderRadius: 12, padding: 24,
        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
          📝 采集记录 ({total})
        </h2>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>加载中...</div>
        ) : collected.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>📭</div>
            <div>暂无采集记录</div>
            <div style={{ fontSize: 13, marginTop: 4 }}>安装插件后浏览抖音，点击 ⭐ 按钮开始采集</div>
          </div>
        ) : (
          <>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#f5f5f5' }}>
                  <th style={{ padding: '10px 12px', textAlign: 'left' }}>标题</th>
                  <th style={{ padding: '10px 12px', textAlign: 'left' }}>作者</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>❤️ 点赞</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>💬 评论</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>⭐ 收藏</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>🔗 转发</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center' }}>链接</th>
                </tr>
              </thead>
              <tbody>
                {collected.map((v, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '10px 12px', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {v.title || '未命名'}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#666', fontSize: 13 }}>
                      {v.author || '-'}
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>{formatNumber(v.likes)}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>{formatNumber(v.comments)}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>{formatNumber(v.collects)}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>{formatNumber(v.shares)}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      {v.url ? (
                        <a href={v.url} target="_blank" rel="noopener noreferrer" style={{ color: '#667eea', textDecoration: 'none' }}>
                          🔗
                        </a>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* 分页 */}
            {total > 20 && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  style={{ padding: '6px 16px', borderRadius: 6, border: '1px solid #ddd', background: '#fff', cursor: 'pointer' }}
                >
                  上一页
                </button>
                <span style={{ padding: '6px 12px', fontSize: 14, color: '#666' }}>
                  {page} / {Math.ceil(total / 20)}
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= Math.ceil(total / 20)}
                  style={{ padding: '6px 16px', borderRadius: 6, border: '1px solid #ddd', background: '#fff', cursor: 'pointer' }}
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
