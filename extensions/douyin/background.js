/**
 * EchoFlow 爆款采集助手 - Background Script
 */

const ECHOFLOW_API = 'http://localhost:8000/api/platform';

// 监听安装事件
chrome.runtime.onInstalled.addListener(() => {
  console.log('[EchoFlow] 爆款采集助手已安装');
  // 初始化本地收藏列表
  chrome.storage.local.set({ collected: [] });
});

// 监听来自 content script 和 popup 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'collectVideo') {
    collectVideo(request.data).then(sendResponse);
    return true;
  }

  if (request.action === 'getCollected') {
    chrome.storage.local.get('collected', (result) => {
      sendResponse(result.collected || []);
    });
    return true;
  }

  if (request.action === 'syncToBackend') {
    syncToBackend().then(sendResponse);
    return true;
  }
});

// 采集视频（存本地 + 尝试同步后端）
async function collectVideo(video) {
  try {
    // 存到本地
    const { collected = [] } = await chrome.storage.local.get('collected');
    
    // 去重（按 URL）
    const exists = collected.some(v => v.url === video.url);
    if (exists) {
      return { success: true, message: '已采集过该视频' };
    }

    collected.unshift(video);
    // 最多保存 500 条
    if (collected.length > 500) collected.pop();
    await chrome.storage.local.set({ collected });

    // 尝试同步到后端
    try {
      const res = await fetch(`${ECHOFLOW_API}/collect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: 'douyin', video }),
      });
      if (res.ok) {
        return { success: true, message: '已采集并同步' };
      }
    } catch (e) {
      // 后端没启动也没关系，本地已保存
    }

    return { success: true, message: '已采集（本地）' };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// 同步本地数据到后端
async function syncToBackend() {
  try {
    const { collected = [] } = await chrome.storage.local.get('collected');
    if (collected.length === 0) {
      return { success: false, error: '没有待同步的数据' };
    }

    const res = await fetch(`${ECHOFLOW_API}/collect/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform: 'douyin', videos: collected }),
    });

    if (res.ok) {
      const result = await res.json();
      return { success: true, ...result };
    }
    return { success: false, error: '同步失败' };
  } catch (err) {
    return { success: false, error: '无法连接 EchoFlow 后端' };
  }
}
