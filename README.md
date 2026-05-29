# EchoFlow AI 🚀

> AI Native Content Growth Operating System — v1.3 多平台对接版

EchoFlow AI 是一个面向内容创作者的自主式 AI 增长系统。它的核心不是"帮你写一篇内容"，而是**"帮你运营一个账号"**。

**核心循环**：生成 → 发布 → 分析 → 优化 → 增长

## ✨ v1.3 新增功能

### 🔗 多平台对接（核心能力升级）
| 功能 | 说明 |
|------|------|
| 统一平台适配器 | `PlatformAdapter` 抽象基类，支持小红书/抖音/视频号 |
| 一键发布 | 选择内容 → 选平台 → 一键发布，支持 Mock 和真实模式切换 |
| Cookie 加密存储 | Fernet 加密，账号凭证安全持久化到 MongoDB |
| 发布历史管理 | 完整的发布记录追踪，状态/链接/错误信息 |
| 数据回流 | 自动抓取已发布内容的阅读/点赞/评论/分享/收藏指标 |
| 账号管理 | 绑定/解绑平台账号，Cookie 过期自动检测 |

### 📡 支持的平台
| 平台 | 发布 | 数据采集 | 说明 |
|------|------|---------|------|
| 小红书 | ✅ | ✅ | 图文笔记发布 + 指标采集 |
| 抖音 | ⚠️ | ✅ | 视频发布需创作者中心，数据采集已支持 |
| 视频号 | ⚠️ | ✅ | 视频发布需视频号助手，数据采集已支持 |

### 🆕 新增页面
| 页面 | 说明 |
|------|------|
| 多平台发布 | 选择平台 → 填写标题/内容/标签 → 一键发布，实时查看发布历史 |
| 账号管理 | 绑定/解绑平台账号，Cookie 获取引导，加密存储状态展示 |

### 🔐 安全设计
- Cookie 使用 Fernet 对称加密，密钥持久化到 `data/.secret_key`
- 文件权限 0o600，仅当前用户可读
- Cookie 仅用于平台 API 调用，不会外传

## ✨ v1.2 新增功能

### 🎬 3D 数据大屏（沉浸式可视化）
| 功能 | 说明 |
|------|------|
| Three.js 3D 场景 | 粒子场 + 发光二十面体 + 轨道环 + 数据柱 + 星空背景 |
| 6 大 KPI 卡片 | 翻牌数字动画，实时数据脉冲效果 |
| 7 张交互图表 | ECharts 6.1 驱动，统一 neon 暗色主题 |
| 全屏模式 | 无干扰数据大屏体验 |
| 实时活动流 | 自动轮播系统动态 |

### 📊 大屏包含的图表
| 图表 | 类型 | 说明 |
|------|------|------|
| 用户增长趋势 | 面积图 | 抖音/小红书/B站 三平台近 7 天 |
| 平台粉丝分布 | 环形图 | 各平台粉丝占比 |
| 内容表现对比 | 分组柱状图 | 播放/点赞/评论/分享 |
| 互动率雷达 | 雷达图 | 当前 vs 上期对比 |
| 内容转化漏斗 | 条形图 | 曝光→播放→完播→点赞→关注 |
| 24h 活跃时段 | 折线图 | 用户活跃热力分布 |
| TOP5 爆款内容 | 排行表 | 实时排序 |

## ✨ v1.1 功能

### 🧠 策略智能体（核心大脑）
| 功能 | 说明 |
|------|------|
| 创作者阶段识别 | 自动判断冷启动 / 成长期 / 瓶颈期 / 成熟期 |
| 增长目标拆解 | 将目标拆解为可执行的里程碑和行动项 |
| 内容方向规划 | 基于平台算法和数据，规划最优内容方向 |
| 发布策略制定 | 频率、时间、节奏的完整方案 |
| 钩子 & 互动策略 | 提升 CTR 和互动率的具体策略 |
| 风险预警 | 识别潜在风险并提供应对方案 |

### 🔄 增长反馈闭环（核心竞争力）
| 功能 | 说明 |
|------|------|
| 表现诊断 | 基于历史数据自动诊断内容表现问题 |
| 策略自动优化 | 分析结果自动转化为策略调整建议 |
| Prompt 自动优化 | 为各智能体生成 Prompt 优化建议 |
| 下一步行动 | 自动生成可执行的行动计划 |

### 🧠 四层记忆系统
| 记忆层 | 说明 |
|--------|------|
| 用户记忆 | 创作者画像、风格偏好 |
| 增长记忆 | 爆款历史、失败案例、成功因素 |
| 策略记忆 | 策略历史、Prompt 版本管理 |
| 工作流记忆 | Agent 状态、任务日志 |

### ⚡ 智能 LLM 路由
| 任务类型 | 推荐模型 | 原因 |
|----------|----------|------|
| 分类与标签 | Qwen | 性价比高，速度快 |
| 文案与脚本 | DeepSeek | 创意能力强 |
| 数据分析 | GPT-4o | 综合能力好 |
| 复杂推理 | GPT-4o | 能力最全面 |

> 自动按任务类型选择最优模型，API Key 未配置时自动降级。

## ✨ 全功能概览

### Phase 1 · 基础
| 功能 | 说明 |
|------|------|
| 🎯 爆款标题生成 | 输入选题 → 多个高 CTR 标题方案（含评分、情绪标签、解析） |
| ✨ 标题优化 | 输入标题 → 多个优化方案 + 改进点分析 |

### Phase 2 · 趋势反馈
| 功能 | 说明 |
|------|------|
| 📈 趋势分析 | 热门话题发现 + 爆款模式分析 + 受众洞察（集成实时平台数据） |
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

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│  热搜 │ 趋势 │ 策略 │ 标题 │ 脚本 │ 封面 │ 发布 │ 增长闭环 │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────┐
│              Backend (FastAPI) — 30+ API             │
├─────────────────────────────────────────────────────┤
│                   Agent Layer                        │
│  管理智能体 ← 策略智能体(🧠核心大脑)                │
│  ├── 选题 │ 钩子 │ 趋势 │ 评论 │ 脚本               │
│  ├── 封面 │ 发布 │ 分析 │ 记忆                       │
│  └── 增长反馈闭环 (🔄 核心竞争力)                    │
├─────────────────────────────────────────────────────┤
│              Smart LLM Router                        │
│  Qwen(分类) │ DeepSeek(创意) │ GPT-4o(推理) │ Mimo   │
├─────────────────────────────────────────────────────┤
│              Memory Layer (四层记忆)                  │
│  用户记忆 │ 增长记忆 │ 策略记忆 │ 工作流记忆          │
├─────────────────────────────────────────────────────┤
│              Data Layer                              │
│  MongoDB(持久化) │ Redis(缓存) │ MCP Servers │ 爬虫   │
└─────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite 5 + TailwindCSS 3 |
| 后端 | Python 3.10+ + FastAPI |
| 智能体 | 10 个专业智能体 + LangGraph 工作流 |
| LLM | Qwen / DeepSeek / GPT / Mimo（智能路由） |
| 数据 | MCP 协议 + 爬虫（B站/抖音/小红书/微博） |
| 存储 | MongoDB（持久化）+ Redis（缓存） |

## 🚀 快速开始

### 0. 基础服务（MongoDB & Redis）

系统使用 MongoDB 存储数据，Redis 做缓存，启动前需确保两个服务正在运行。

> **前提**：已安装 Homebrew，MongoDB 和 Redis 均通过 Homebrew 管理。

```bash
# ── 首次安装 ──────────────────────────────────
brew install redis
# MongoDB 如果未安装：brew install mongodb-community

# ── 启动服务 ──────────────────────────────────
brew services start redis
brew services start mongodb-community

# ── 关闭服务（不用时关闭，避免占用资源）────────
brew services stop redis
brew services stop mongodb-community

# ── 查看状态 ──────────────────────────────────
brew services list | grep -E "redis|mongo"

# ── 验证连接 ──────────────────────────────────
redis-cli ping          # 应返回 PONG
mongosh --eval "db.runCommand({ping:1})" --quiet  # 应返回 { ok: 1 }
```

> 💡 **提示**：不需要时记得 `brew services stop` 关闭，不会一直占后台资源。

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

打开浏览器访问 `http://localhost:3000`，从**策略中心**开始制定增长策略！

## 📁 项目结构

```
EchoFlow-AI/
├── backend/
│   ├── main.py                 # FastAPI 入口 (30+ API 路由)
│   ├── agents/
│   │   ├── base.py             # LLM 抽象层 + 智能路由
│   │   ├── manager.py          # 管理智能体 (任务编排核心)
│   │   ├── strategy_agent.py   # 🧠 策略智能体 (v1.1 核心大脑)
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
│   │   ├── title_workflow.py   # LangGraph 标题工作流
│   │   └── growth_loop.py      # 🔄 增长反馈闭环 (v1.1)
│   ├── models/
│   │   └── schemas.py          # Pydantic 数据模型
│   ├── memory/
│   │   └── store.py            # 四层记忆存储 (v1.1)
│   ├── crawlers/               # 平台爬虫 (三级降级)
│   ├── mcp_clients/            # MCP 协议客户端
│   ├── configs/
│   │   └── platforms.json      # 5 个平台特性配置
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx             # 13 个功能面板
│       ├── api/client.js       # API 调用层
│       └── components/
│           ├── StrategyPanel.jsx    # 🧠 策略中心 (v1.1)
│           ├── GrowthLoopPanel.jsx  # 🔄 增长闭环 (v1.1)
│           ├── HotSearchPanel.jsx   # 实时热搜
│           ├── TrendPanel.jsx       # 趋势分析
│           ├── GeneratePanel.jsx    # 标题生成
│           ├── ScriptPanel.jsx      # 脚本生成
│           ├── CoverPanel.jsx       # 封面设计
│           ├── PublishPanel.jsx     # 发布策略
│           ├── PipelinePanel.jsx    # 全流程
│           ├── AnalyticsPanel.jsx   # 数据分析
│           ├── FeedbackPanel.jsx    # 评论分析
│           └── HistoryPanel.jsx     # 历史记录
├── mcp-servers/
│   ├── bilibili-mcp-server/    # B站 MCP Server
│   └── dailyhot-api/           # 60+ 平台热搜聚合
└── README.md
```

## 🔌 API 接口

### v1.1 新增
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/strategy` | 🧠 策略生成（核心大脑） |
| POST | `/api/growth-loop` | 🔄 增长反馈闭环 |
| GET | `/api/growth-stats` | 增长统计数据 |
| POST | `/api/growth-memories` | 保存增长记忆 |
| GET | `/api/growth-memories` | 获取增长记忆 |
| POST | `/api/strategy-memories` | 保存策略记忆 |
| GET | `/api/strategy-memories` | 获取策略记忆 |
| GET | `/api/active-prompts` | 获取活跃 Prompt 版本 |

### Phase 1-4
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/generate` | 生成爆款标题 |
| POST | `/api/optimize` | 优化标题 |
| POST | `/api/trends` | 趋势分析 |
| POST | `/api/feedback` | 评论分析 |
| POST | `/api/script` | 脚本生成 |
| POST | `/api/cover` | 封面文案生成 |
| POST | `/api/publish` | 发布策略 |
| POST | `/api/pipeline` | 全流程生产 |
| POST | `/api/analytics` | 数据分析 |
| POST/GET | `/api/profiles` | 创作者画像 CRUD |
| GET | `/api/memories` | 内容记忆 |
| POST | `/api/memories/search` | 搜索记忆 |

### 通用
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/platforms` | 获取平台列表 |
| GET | `/api/hot/{platform}` | 实时热搜 |
| GET | `/api/history` | 历史记录 |
| DELETE | `/api/history/{id}` | 删除记录 |

## 🤖 多智能体架构

```
用户输入
    │
    ▼
管理智能体 (manager) ── 任务分解 & 编排
    │
    ├── 🧠 策略智能体 (strategy_agent) ── 核心大脑
    ├── 选题生成智能体 (topic_agent)
    ├── 钩子优化智能体 (hook_agent)
    ├── 趋势分析智能体 (trend_agent)
    ├── 评论分析智能体 (feedback_agent)
    ├── 脚本生成智能体 (script_agent)
    ├── 封面文案智能体 (cover_agent)
    ├── 发布策略智能体 (publish_agent)
    ├── 数据分析智能体 (analytics_agent)
    ├── 记忆智能体 (memory_agent)
    │
    └── 🔄 增长反馈闭环
         分析 → 优化策略 → 优化 Prompt → 生成内容
```

## 📜 License

MIT
