# EchoFlow AI 🚀

> AI Native Content Growth Operating System — v2.1 爆款采集版

EchoFlow AI 是一个面向内容创作者的自主式 AI 增长系统。它的核心不是"帮你写一篇内容"，而是**"帮你运营一个账号"**。

**核心循环**：生成 → 发布 → 分析 → 优化 → 增长

---

## ✨ 版本历程

| 版本 | 核心能力 |
|------|----------|
| **v2.2** | 🎨 LLM 模型自由选择 — 顶部栏一键切换 Qwen / DeepSeek / GPT-4o / Mimo |
| **v2.1** | 🔌 抖音爆款采集浏览器插件、平台数据同步、修复引导页交互 |
| **v2.0** | 🔐 用户认证系统、团队管理、成本追踪、AB 测试、竞品监控、归档管理 |
| **v1.4** | 📊 DRG 审核、每日摘要、数据分析面板、定时任务调度、告警系统 |
| **v1.3** | 🔗 多平台对接、一键发布、Cookie 加密存储、数据回流 |
| **v1.2** | 🎬 3D 数据大屏、ECharts 可视化、全屏模式 |
| **v1.1** | 🧠 策略智能体、增长反馈闭环、四层记忆系统、智能 LLM 路由 |

---

## ✨ v2.1 新增功能

### 🎨 LLM 模型自由选择（v2.2）

| 功能 | 说明 |
|------|------|
| 顶部栏选择器 | Header 右侧 LLM 标签，点击下拉切换模型，显示模型名称和型号 |
| 全局生效 | 选择后所有 12 个 AI 面板（标题生成、趋势分析、脚本生成等）自动使用该模型 |
| 自动发现 | 后端根据 `.env` 中已配置的 API Key 自动返回可用模型列表，无需手动维护 |
| 持久化选择 | 用户选择保存在 localStorage，刷新页面后仍然生效 |
| 智能降级 | 未配置 API Key 的模型不会出现在列表中，选中的模型无 Key 时自动降级到默认模型 |

**支持的模型**：

| 提供商 | 环境变量 | 默认模型 |
|--------|---------|---------|
| 通义千问 | `QWEN_API_KEY` | `qwen-turbo` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| GPT-4o | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Mimo | `MIMO_API_KEY` | `mimo-v2.5-pro` |

**配置方式**：在 `backend/.env` 中填入对应 API Key 即可启用：

```bash
# 只填你想用的即可，前端会自动只显示已配置的模型
MIMO_API_KEY=your_key_here
QWEN_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
DEFAULT_LLM_PROVIDER=mimo   # 未手动选择时的默认模型
```

### 🔌 抖音爆款采集（浏览器插件）
| 功能 | 说明 |
|------|------|
| 浮动采集按钮 | 在抖音页面右下角显示 ⭐ 按钮，一键采集当前视频 |
| 自动提取数据 | 标题、作者、点赞数、评论数、收藏数、转发数、URL |
| 本地存储 | 使用 chrome.storage.local 本地保存，最多 500 条 |
| 后端同步 | 一键同步到 EchoFlow 后端，支持批量上传 |
| 去重机制 | 基于 URL 自动去重，避免重复采集 |

### 📊 平台数据同步模块
| API | 说明 |
|-----|------|
| `POST /api/platform/collect` | 采集单条视频数据 |
| `POST /api/platform/collect/batch` | 批量采集（插件同步） |
| `GET /api/platform/collect/list` | 查看采集列表（分页） |
| `POST /api/platform/import/csv` | 导入平台 CSV 数据（抖音/哔哩哔哩格式） |
| `POST /api/platform/sync` | 通用平台数据同步 |

### 🖥️ 前端爆款采集面板
| 功能 | 说明 |
|------|------|
| 采集统计 | 总数、今日采集、分平台统计 |
| 采集记录表 | 标题、作者、互动数据、平台标签、跳转链接 |
| 使用说明 | 插件安装和使用指引 |
| 分页浏览 | 支持分页查看历史采集记录 |

---

## ✨ v2.0 核心功能

### 🔐 用户认证系统
| 功能 | 说明 |
|------|------|
| 用户注册/登录 | JWT Token 认证，bcrypt 密码加密 |
| 角色权限 | admin / editor / viewer 三级角色 |
| 资源权限 | content:create、account:bind、abtest:manage 等细粒度控制 |
| 引导流程 | 新用户快速上手引导（可跳过） |

### 👥 团队协作
| 功能 | 说明 |
|------|------|
| 成员管理 | 邀请/移除团队成员 |
| 角色分配 | 管理员/编辑者/查看者 |
| 协作日志 | 操作记录追踪 |

### 💰 成本追踪
| 功能 | 说明 |
|------|------|
| Token 消耗统计 | 按模型/任务类型统计 LLM 调用成本 |
| 预算管理 | 设置预算上限，超支告警 |
| 成本报表 | 日/周/月成本趋势分析 |

### 🧪 AB 测试
| 功能 | 说明 |
|------|------|
| 多变量测试 | 标题/封面/发布时间等变量对比 |
| 效果评估 | 点击率/互动率/转化率对比分析 |
| 智能推荐 | 基于测试结果推荐最优方案 |

### 📡 竞品监控
| 功能 | 说明 |
|------|------|
| 竞品追踪 | 监控竞品账号内容发布动态 |
| 对比分析 | 内容策略、发布频率、互动数据对比 |
| 差异化建议 | 基于竞品分析提供差异化内容策略 |

### 📦 归档管理
| 功能 | 说明 |
|------|------|
| 内容归档 | 历史内容分类归档 |
| 版本管理 | 内容修改历史追踪 |
| 快速检索 | 按标签/平台/时间检索历史内容 |

---

## ✨ v1.x 基础功能

### 🧠 策略智能体（核心大脑）
| 功能 | 说明 |
|------|------|
| 创作者阶段识别 | 自动判断冷启动 / 成长期 / 瓶颈期 / 成熟期 |
| 增长目标拆解 | 将目标拆解为可执行的里程碑和行动项 |
| 内容方向规划 | 基于平台算法和数据，规划最优内容方向 |
| 发布策略制定 | 频率、时间、节奏的完整方案 |
| 钩子 & 互动策略 | 提升 CTR 和互动率的具体策略 |
| 风险预警 | 识别潜在风险并提供应对方案 |

### 🔄 增长反馈闭环
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

### 🎬 3D 数据大屏
| 功能 | 说明 |
|------|------|
| Three.js 3D 场景 | 粒子场 + 发光二十面体 + 轨道环 + 数据柱 + 星空背景 |
| 6 大 KPI 卡片 | 翻牌数字动画，实时数据脉冲效果 |
| 7 张交互图表 | ECharts 6.1 驱动，统一 neon 暗色主题 |
| 全屏模式 | 无干扰数据大屏体验 |

### 📡 多平台对接
| 平台 | 发布 | 数据采集 | 说明 |
|------|------|---------|------|
| 小红书 | ✅ | ✅ | 图文笔记发布 + 指标采集 |
| 抖音 | ⚠️ | ✅ | 视频发布需创作者中心，数据采集已支持 |
| 视频号 | ⚠️ | ✅ | 视频发布需视频号助手，数据采集已支持 |
| B站 | - | ✅ | 数据采集已支持 |
| 微博 | - | ✅ | 数据采集已支持 |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React 18 + Vite 5)             │
│  数据大屏 │ 策略 │ 趋势 │ 标题 │ 脚本 │ 封面 │ 发布 │ 增长闭环 │
│  竞品监控 │ AB测试 │ 成本 │ 团队 │ 归档 │ 爆款采集 │ 平台同步  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                Backend (FastAPI) — 50+ API                   │
├─────────────────────────────────────────────────────────────┤
│                     Agent Layer                              │
│  管理智能体 ← 策略智能体(🧠核心大脑)                        │
│  ├── 选题 │ 钩子 │ 趋势 │ 评论 │ 脚本                       │
│  ├── 封面 │ 发布 │ 分析 │ 记忆                               │
│  └── 增长反馈闭环 (🔄 核心竞争力)                            │
├─────────────────────────────────────────────────────────────┤
│                Smart LLM Router                              │
│  Qwen(分类) │ DeepSeek(创意) │ GPT-4o(推理) │ Mimo           │
├─────────────────────────────────────────────────────────────┤
│                Memory Layer (四层记忆)                        │
│  用户记忆 │ 增长记忆 │ 策略记忆 │ 工作流记忆                  │
├─────────────────────────────────────────────────────────────┤
│                Data Layer                                    │
│  MongoDB(持久化) │ Redis(缓存) │ MCP Servers │ 爬虫           │
├─────────────────────────────────────────────────────────────┤
│                Browser Extension                             │
│  抖音爆款采集插件 → chrome.storage → 后端同步                 │
└─────────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite 5 + TailwindCSS 3 |
| 后端 | Python 3.12 + FastAPI |
| 智能体 | 10 个专业智能体 + LangGraph 工作流 |
| LLM | Qwen / DeepSeek / GPT / Mimo（智能路由） |
| 数据 | MCP 协议 + 爬虫（B站/抖音/小红书/微博） |
| 存储 | MongoDB（持久化）+ Redis（缓存） |
| 浏览器插件 | Chrome Manifest V3（抖音爆款采集） |

---

## 🚀 快速开始

### 0. 基础服务（MongoDB & Redis）

```bash
# ── 启动服务 ──────────────────────────────────
brew services start redis
brew services start mongodb-community

# ── 关闭服务 ──────────────────────────────────
brew services stop redis
brew services stop mongodb-community

# ── 验证连接 ──────────────────────────────────
redis-cli ping
mongosh --eval "db.runCommand({ping:1})" --quiet
```

### 1. 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 启动后端
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

后端运行在 `http://localhost:8000`，API 文档：`http://localhost:8000/docs`

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:3000`

### 3. 浏览器插件（爆款采集）

1. 打开 Chrome，访问 `chrome://extensions/`
2. 开启「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择 `extensions/douyin/` 文件夹
5. 打开抖音网页版（douyin.com），右下角出现 ⭐ 按钮即可使用

### 4. 使用

打开浏览器访问 `http://localhost:3000`，使用以下账号登录：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

---

## 📁 项目结构

```
EchoFlow-AI/
├── backend/
│   ├── main.py                 # FastAPI 入口 (50+ API 路由)
│   ├── agents/                 # 10 个专业智能体
│   │   ├── base.py             # LLM 抽象层 + 智能路由
│   │   ├── manager.py          # 管理智能体 (任务编排核心)
│   │   ├── strategy_agent.py   # 🧠 策略智能体 (核心大脑)
│   │   └── ...                 # 其他智能体
│   ├── workflows/              # LangGraph 工作流
│   ├── models/                 # Pydantic 数据模型
│   ├── memory/                 # 四层记忆存储
│   ├── platforms/              # 平台适配器 + 数据同步
│   │   ├── adapters.py         # 平台适配器（发布/采集）
│   │   ├── manager.py          # 账号管理（Cookie 加密）
│   │   └── sync_router.py      # 🔌 爆款采集 API (v2.1)
│   ├── auth/                   # 🔐 用户认证 (v2.0)
│   ├── team/                   # 👥 团队管理 (v2.0)
│   ├── cost/                   # 💰 成本追踪 (v2.0)
│   ├── abtest/                 # 🧪 AB 测试 (v2.0)
│   ├── competitor/             # 📡 竞品监控 (v2.0)
│   ├── archive/                # 📦 归档管理 (v2.0)
│   ├── scheduler/              # ⏰ 定时任务 (v1.4)
│   ├── alerts/                 # 🚨 告警系统 (v1.4)
│   ├── analytics/              # 📊 数据分析 (v1.4)
│   ├── daily_digest/           # 📰 每日摘要 (v1.4)
│   ├── onboarding/             # 🎯 引导流程 (v2.0)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx             # 20+ 功能面板
│       ├── api/
│       │   └── client.js       # API 客户端（50+ 接口）
│       ├── utils/
│       │   └── llmProvider.js  # 🎨 LLM 模型选择状态管理 (v2.2)
│       └── components/
│           ├── Header.jsx          # 🎨 LLM 模型下拉选择器 (v2.2)
│           ├── DashboardPage.jsx    # 🎬 3D 数据大屏
│           ├── StrategyPanel.jsx    # 🧠 策略中心
│           ├── GrowthLoopPanel.jsx  # 🔄 增长闭环
│           ├── PlatformSyncPanel.jsx # 🔌 爆款采集 (v2.1)
│           ├── TeamPanel.jsx        # 👥 团队管理
│           ├── CostPanel.jsx        # 💰 成本追踪
│           ├── ABTestPanel.jsx      # 🧪 AB 测试
│           ├── CompetitorPanel.jsx  # 📡 竞品监控
│           └── ...                  # 其他面板
├── extensions/
│   └── douyin/                 # 🔌 抖音爆款采集插件 (v2.1)
│       ├── manifest.json       # Chrome 扩展配置
│       ├── content.js          # 页面内容提取
│       ├── background.js       # 后台存储 + 同步
│       ├── popup.html/js       # 弹窗界面
│       └── icons/              # 插件图标
├── mcp-servers/                # MCP 协议服务
└── README.md
```

---

## 🔌 API 接口（50+）

### 认证 & 用户 (v2.0)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 系统 & LLM (v2.2)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/providers` | 获取可用 LLM 提供商列表（仅返回已配置 API Key 的） |
| GET | `/api/health` | 健康检查 |
| GET | `/api/monitoring` | 系统监控指标 |

### 平台数据同步 (v2.1)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/platform/collect` | 采集单条视频 |
| POST | `/api/platform/collect/batch` | 批量采集 |
| GET | `/api/platform/collect/list` | 查看采集列表 |
| POST | `/api/platform/import/csv` | 导入 CSV 数据 |
| POST | `/api/platform/sync` | 通用平台同步 |
| GET | `/api/platform/data` | 获取所有同步数据 |

### 策略 & 增长 (v1.1)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/strategy` | 🧠 策略生成 |
| POST | `/api/growth-loop` | 🔄 增长反馈闭环 |
| GET | `/api/growth-stats` | 增长统计数据 |

### 内容创作 (Phase 1-4)
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

### 运营管理 (v2.0)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/team/*` | 团队管理 |
| GET/POST | `/api/cost/*` | 成本追踪 |
| GET/POST | `/api/abtest/*` | AB 测试 |
| GET/POST | `/api/competitor/*` | 竞品监控 |
| GET/POST | `/api/archive/*` | 归档管理 |
| GET/POST | `/api/scheduler/*` | 定时任务 |
| GET/POST | `/api/alerts/*` | 告警系统 |
| GET | `/api/dashboard` | 数据大屏 |
| GET | `/api/onboarding/status` | 引导状态 |

---

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
