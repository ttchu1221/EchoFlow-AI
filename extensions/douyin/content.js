/**
 * EchoFlow 爆款采集助手 - Content Script
 * 在抖音页面上添加"采集"按钮
 */

// 从当前页面提取视频信息
function extractCurrentVideo() {
  const url = window.location.href;
  
  // 提取标题 - 抖音视频页通常有标题文本
  const titleEl = document.querySelector(
    '[class*="title"], [class*="desc"], h1, [data-e2e="video-desc"]'
  );
  
  // 提取作者
  const authorEl = document.querySelector(
    '[class*="author"], [class*="nickname"], [data-e2e="user-info"] [class*="name"]'
  );
  
  // 提取互动数据
  const getText = (selectors) => {
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el) return el.textContent.trim();
    }
    return '0';
  };

  const parseNum = (text) => {
    if (!text) return 0;
    text = text.trim();
    if (text.includes('万')) return Math.round(parseFloat(text) * 10000);
    if (text.includes('亿')) return Math.round(parseFloat(text) * 100000000);
    return parseInt(text.replace(/[^0-9]/g, '')) || 0;
  };

  // 尝试获取点赞、评论、收藏、转发数
  const likesText = getText(['[data-e2e="digg-count"]', '[class*="like"] [class*="count"]', '[class*="zan"]']);
  const commentsText = getText(['[data-e2e="comment-count"]', '[class*="comment"] [class*="count"]']);
  const collectText = getText(['[data-e2e="collect-count"]', '[class*="collect"] [class*="count"]', '[class*="收藏"]']);
  const shareText = getText(['[data-e2e="share-count"]', '[class*="share"] [class*="count"]', '[class*="转发"]']);

  return {
    title: titleEl?.textContent?.trim()?.slice(0, 200) || document.title || '',
    author: authorEl?.textContent?.trim() || '',
    url: url,
    likes: parseNum(likesText),
    comments: parseNum(commentsText),
    collects: parseNum(collectText),
    shares: parseNum(shareText),
    collected_at: new Date().toISOString(),
  };
}

// 创建浮动采集按钮
function createCollectButton() {
  // 避免重复创建
  if (document.getElementById('echowflow-collect-btn')) return;

  const btn = document.createElement('div');
  btn.id = 'echowflow-collect-btn';
  btn.innerHTML = '⭐';
  btn.title = '采集到 EchoFlow';
  btn.style.cssText = `
    position: fixed;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    cursor: pointer;
    z-index: 99999;
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
    transition: all 0.2s;
    user-select: none;
  `;

  btn.addEventListener('mouseenter', () => {
    btn.style.transform = 'translateY(-50%) scale(1.1)';
  });
  btn.addEventListener('mouseleave', () => {
    btn.style.transform = 'translateY(-50%) scale(1)';
  });

  btn.addEventListener('click', async () => {
    const video = extractCurrentVideo();
    
    btn.innerHTML = '⏳';
    btn.style.pointerEvents = 'none';

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'collectVideo',
        data: video,
      });

      if (response?.success) {
        btn.innerHTML = '✅';
        btn.style.background = 'linear-gradient(135deg, #4ade80, #22c55e)';
        showTip('已采集！');
      } else {
        btn.innerHTML = '❌';
        btn.style.background = 'linear-gradient(135deg, #f87171, #ef4444)';
        showTip(response?.error || '采集失败');
      }
    } catch (err) {
      btn.innerHTML = '❌';
      btn.style.background = 'linear-gradient(135deg, #f87171, #ef4444)';
      showTip('请先启动 EchoFlow');
    }

    setTimeout(() => {
      btn.innerHTML = '⭐';
      btn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
      btn.style.pointerEvents = 'auto';
    }, 2000);
  });

  document.body.appendChild(btn);
}

// 显示提示
function showTip(text) {
  const tip = document.createElement('div');
  tip.textContent = text;
  tip.style.cssText = `
    position: fixed;
    right: 80px;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(0,0,0,0.8);
    color: #fff;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 14px;
    z-index: 99999;
    animation: echowflowFadeIn 0.3s;
  `;
  document.body.appendChild(tip);
  setTimeout(() => tip.remove(), 2000);
}

// 监听来自 popup 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractData') {
    const video = extractCurrentVideo();
    sendResponse({ success: true, data: video });
  }
  return true;
});

// 页面加载后创建按钮
if (window.location.href.includes('douyin.com')) {
  setTimeout(createCollectButton, 2000);
}

console.log('[EchoFlow] 爆款采集助手已加载');
