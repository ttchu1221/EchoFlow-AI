/**
 * EchoFlow 爆款采集助手 - Popup Script
 */

function formatNumber(num) {
  if (!num && num !== 0) return '0';
  num = Number(num) || 0;
  if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
  if (num >= 10000) return (num / 10000).toFixed(1) + '万';
  return num.toLocaleString();
}

function showResult(id, msg, ok = true) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = `result ${ok ? 'ok' : 'err'}`;
  setTimeout(() => { el.className = 'result'; }, 3000);
}

// 加载采集列表
async function loadCollected() {
  const { collected = [] } = await chrome.storage.local.get('collected');
  
  // 更新统计
  document.getElementById('totalCount').textContent = collected.length;
  
  const today = new Date().toISOString().slice(0, 10);
  const todayCount = collected.filter(v => v.collected_at?.startsWith(today)).length;
  document.getElementById('todayCount').textContent = todayCount;

  // 更新列表
  const list = document.getElementById('videoList');
  if (collected.length === 0) {
    list.innerHTML = '<div class="empty">暂无采集记录</div>';
    return;
  }

  list.innerHTML = collected.slice(0, 20).map(v => `
    <div class="video-item">
      ${v.author ? `<div class="author">@ ${v.author}</div>` : ''}
      <div class="title">${v.title || '未命名视频'}</div>
      <div class="meta">
        <span>❤️ ${formatNumber(v.likes)}</span>
        <span>💬 ${formatNumber(v.comments)}</span>
        <span>⭐ ${formatNumber(v.collects)}</span>
        <span>🔗 ${formatNumber(v.shares)}</span>
      </div>
    </div>
  `).join('');
}

// 采集当前页面
async function extractCurrent() {
  const btn = document.getElementById('extractBtn');
  btn.disabled = true;
  btn.textContent = '⏳ 采集中...';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // 注入脚本
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js'],
      });
    } catch (e) {}

    await new Promise(r => setTimeout(r, 500));

    const response = await chrome.tabs.sendMessage(tab.id, { action: 'extractData' });
    
    if (response?.success) {
      // 保存到本地
      const video = response.data;
      const { collected = [] } = await chrome.storage.local.get('collected');
      const exists = collected.some(v => v.url === video.url);
      
      if (!exists) {
        collected.unshift(video);
        await chrome.storage.local.set({ collected });
        showResult('extractResult', '✅ 采集成功！');
      } else {
        showResult('extractResult', '已采集过该视频');
      }
      loadCollected();
    } else {
      showResult('extractResult', '采集失败: ' + (response?.error || '未知错误'), false);
    }
  } catch (err) {
    showResult('extractResult', '采集失败: ' + err.message, false);
  }

  btn.disabled = false;
  btn.textContent = '📷 采集当前页面';
}

// 同步到后端
async function syncToBackend() {
  const btn = document.getElementById('syncBtn');
  btn.disabled = true;
  btn.textContent = '同步中...';

  try {
    const response = await chrome.runtime.sendMessage({ action: 'syncToBackend' });
    if (response?.success) {
      showResult('syncResult', `✅ ${response.message || '同步成功'}`);
    } else {
      showResult('syncResult', response?.error || '同步失败', false);
    }
  } catch (err) {
    showResult('syncResult', '请先启动 EchoFlow 后端', false);
  }

  btn.disabled = false;
  btn.textContent = '🔄 同步到 EchoFlow';
}

// 事件绑定
document.getElementById('extractBtn').addEventListener('click', extractCurrent);
document.getElementById('syncBtn').addEventListener('click', syncToBackend);

// 初始化
loadCollected();
