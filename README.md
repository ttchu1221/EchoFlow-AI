# EchoFlow AI 🚀

> AI 驱动的内容运营智能体 — 全功能版

EchoFlow AI 是一个基于多智能体协作的自主内容运营系统，覆盖从趋势发现到内容优化的完整工作流程。

## ✨ 全功能概览

### Phase 1 · 基础
| 功能 | 说明 |
|------|------|
| 🎯 爆款标题生成 | 输入选题 → 多个高 CTR 标题方案（含评分、情绪标签、解析） |
| ✨ 标题优化 | 输入标题 → 多个优化方案 + 改进点分析 |

### Phase 2 · 趋势反馈
| 功能 | 说明 |
|------|------|
| 📈 趋势分析 | 热门话题发现 + 爆款模式分析 + 受众洞察 |
| 💬 评论分析 | 情感分析 + 意图识别 + 互动评分 + 改进建议 |

### Phase 3 · 内容生产
| 功能 | 说明 |
|------|------|
| 📝 脚本生成 | 视频脚本 / 小红书文案 / 直播脚本（含分段、拍摄提示） |
| 🎨 封面设计 | 封面主文案 + 副文案 + 布局 + 配色 + 视觉元素建议 |
| 🚀 发布策略 | 最佳发布时间 + 标签优化 + 跨平台分发 + 文案模板 |
| ⚡ 全流程 | 一键生成：标题 + 脚本 + 封面 + 发布策略 |

### Phase 4 · 增长分析
| 功能 | 说明 |
|------|------|
| 📊 数据分析 | 指标解读 + 基准对比 + 增长建议 + 策略总结 |
| 🧠 创作者记忆 | 画像管理 + 内容记忆 + 智能洞察 |

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Vite + TailwindCSS + react-icons |
| 后端 | Python + FastAPI |
| 智能体 | LangGraph 多智能体编排（8 个智能体） |
| LLM | Qwen / DeepSeek / GPT (OpenAI 协议兼容) |
| 存储 | JSON 文件（轻量，可升级） |

## 🚀 快速开始

### 1. 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 启动后端
python main.py
```

后端运行在 `http://localhost:8000`，API 文档：`http://localhost:8000/docs`

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 `http://localhost:3000`

### 3. 使用

打开浏览器访问 `http://localhost:3000`，选择功能模块即可使用！

## 📁 项目结构

```
EchoFlow-AI/
├── backend/
│   ├── main.py                 # FastAPI 入口 (20+ API 路由)
│   ├── agents/
│   │   ├── base.py             # LLM 抽象层 (Qwen/DeepSeek/GPT)
│   │   ├── manager.py          # 管理智能体 (任务编排)
│   │   ├── topic_agent.py      # 选题生成智能体
│   │   ├── hook_agent.py       # 钩子优化智能体
│   │   ├── trend_agent.py      # 趋势分析智能体
│   │   ├── feedback_agent.py   # 评论分析智能体
│   │   ├── script_agent.py     # 脚本生成智能体
│   │   ├── cover_agent.py      # 封面文案智能体
│   │   ├── publish_agent.py    # 发布策略智能体
│   │   ├── analytics_agent.py  # 数据分析智能体
│   │   └── memory_agent.py     # 记忆智能体
│   ├── workflows/
│   │   └── title_workflow.py   # LangGraph 工作流
│   ├── models/
│   │   └── schemas.py          # Pydantic 数据模型
│   ├── memory/
│   │   └── store.py            # 历史记录存储
│   ├── configs/
│   │   └── platforms.json      # 5 个平台特性配置
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx             # 10 个 Tab 切换
│       ├── api/client.js       # API 调用层
│       └── components/         # 10 个功能组件
│           ├── Header.jsx
│           ├── GeneratePanel.jsx
│           ├── OptimizePanel.jsx
│           ├── TrendPanel.jsx
│           ├── FeedbackPanel.jsx
│           ├── ScriptPanel.jsx
│           ├── CoverPanel.jsx
│           ├── PublishPanel.jsx
│           ├── PipelinePanel.jsx
│           ├── AnalyticsPanel.jsx
│           ├── TitleCard.jsx
│           └── HistoryPanel.jsx
└── README.md
```

## 🔌 API 接口

### Phase 1
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/generate` | 生成爆款标题 |
| POST | `/api/optimize` | 优化标题 |

### Phase 2
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/trends` | 趋势分析 |
| POST | `/api/feedback` | 评论分析 |

### Phase 3
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/script` | 脚本生成 |
| POST | `/api/cover` | 封面文案生成 |
| POST | `/api/publish` | 发布策略 |
| POST | `/api/pipeline` | 全流程生产 |

### Phase 4
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/analytics` | 数据分析 |
| POST | `/api/profiles` | 创建/更新创作者画像 |
| GET | `/api/profiles` | 获取所有画像 |
| GET | `/api/memories` | 获取内容记忆 |
| POST | `/api/memories/search` | 搜索记忆 |

### 通用
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/platforms` | 获取平台列表 |
| GET | `/api/history` | 历史记录 |
| DELETE | `/api/history/{id}` | 删除记录 |

## 🤖 多智能体架构

```
用户输入
    │
    ▼
管理智能体 (manager) ── 任务分解 & 编排
    │
    ├── 选题生成智能体 (topic_agent)
    ├── 钩子优化智能体 (hook_agent)
    ├── 趋势分析智能体 (trend_agent)
    ├── 评论分析智能体 (feedback_agent)
    ├── 脚本生成智能体 (script_agent)
    ├── 封面文案智能体 (cover_agent)
    ├── 发布策略智能体 (publish_agent)
    ├── 数据分析智能体 (analytics_agent)
    └── 记忆智能体 (memory_agent)
```

## 📜 License

MIT
