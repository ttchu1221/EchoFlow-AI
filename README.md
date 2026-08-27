# EchoFlow AI Enterprise

## AI Commerce Operating System

> 企业级 AI 电商运营操作系统 · V3.0 Enterprise Edition

---

## 产品定位

**一句话描述：** 帮助企业建立一支由 AI 组成的运营团队。

EchoFlow AI 不再是内容创作工具，而是企业运营 Agent 平台。系统由 7 个专业 AI Agent 协同工作，覆盖电商运营全链路：

```
市场分析 → 竞品监控 → 商品分析 → 广告优化 → 达人合作 → 内容创作 → 数据分析 → 经验学习 → 持续优化
```

---

## 系统架构

```
                        用户（运营人员）
                               │
                               ▼
                   AI COO（总调度 Agent）
                               │
────────────────────────────────────────────────────
│             │              │            │
▼             ▼              ▼            ▼
市场Agent     商品Agent      内容Agent     广告Agent
│             │              │            │
▼             ▼              ▼            ▼
数据分析      SKU分析        文案生成      广告优化
│             │              │            │
────────────────────────────────────────────────────
                ▼
        Analytics Agent
                ▼
        Memory Agent
                ▼
      企业知识持续更新
```

---

## 七大功能层

| 层级 | 名称 | 说明 |
|------|------|------|
| L1 | **Dashboard 企业驾驶舱** | GMV / ROI / 订单 / 广告花费 / AI建议 / Agent状态 |
| L2 | **AI COO 调度中心** | 一句话驱动多Agent协作，自动拆解运营目标 |
| L3 | **Multi-Agent 智能体层** | 7个专业Agent：市场 / 商品 / 内容 / 达人 / 广告 / 分析 / 记忆 |
| L4 | **Workflow Engine 工作流** | 统一的多Agent协作工作流引擎 |
| L5 | **Growth Brain 增长大脑** | 用户记忆 / 爆款规律 / Pattern Memory / Prompt Evolution |
| L6 | **Knowledge 知识中心** | 企业知识库 / 经验积累 / 持续学习 |
| L7 | **Platform 平台层** | 抖音 / 小红书 / 淘宝 / 视频号 / B站 / 微博 |

---

## 七大 AI Agent

| Agent | 职责 | 能力 |
|-------|------|------|
| 🔍 **市场分析 Agent** | 市场趋势 / 热门关键词 / 爆款预测 | 热点追踪 / 趋势分析 / 竞品监控 / 赛道推荐 |
| 📦 **商品分析 Agent** | SKU分析 / 定价策略 / 库存预警 | SKU分析 / 定价优化 / 库存管理 / 退款分析 |
| ✍️ **内容创作 Agent** | 标题生成 / 脚本撰写 / 封面设计 | 标题生成 / 脚本撰写 / 封面设计 / 文案优化 |
| 👤 **达人管理 Agent** | 达人匹配 / 合作效果 / ROI分析 | 达人搜索 / 画像分析 / 合作评估 / 效果追踪 |
| 📊 **广告优化 Agent** | 广告投放 / 预算优化 / ROI提升 | 投放分析 / 预算优化 / 素材建议 / ROI监控 |
| 📈 **数据分析 Agent** | 日报生成 / 效果归因 / 趋势预测 | 日报生成 / 效果归因 / 异常检测 / 趋势预测 |
| 🧠 **记忆学习 Agent** | 经验积累 / 知识图谱 / 持续优化 | 经验记录 / 模式识别 / 知识更新 / 策略优化 |

---

## 前端页面

### 🌐 企业驾驶舱
- 实时 KPI：GMV / ROI / 订单数 / 广告花费
- GMV 7日趋势图
- 平台分布（抖音 / 小红书 / 淘宝 / 视频号）
- AI 智能建议（优先级排序）
- Agent 执行状态监控
- 最近活动日志

### 🤖 AI COO 调度中心
- **任务调度模式**：输入运营目标 → AI自动拆解为多Agent任务
- **对话模式**：与AI COO实时对话，获取运营建议
- 预设目标模板（GMV增长 / 内容推广 / 达人合作 / 广告优化）
- 任务执行状态跟踪

### ⚡ 智能体管理
- 7个Agent的实时状态和指标
- Agent能力标签展示
- 手动触发Agent执行任务
- 任务历史和成功率统计

### 🧠 增长大脑
- 增长记忆库（成功/失败案例）
- 策略库（历史策略记录）
- Prompt进化（活跃Prompt管理）
- 模式发现（置信度评分）
- 知识图谱可视化

### 🛠️ 工具箱（19个专业工具）
- **数据洞察**：实时热搜 / 趋势分析 / 竞品监控 / 每日热点 / 评论分析 / 数据分析
- **内容创作**：标题生成 / 标题优化 / 脚本生成 / 封面设计 / 全流程
- **运营执行**：策略中心 / 发布策略 / 多平台发布 / 内容审核 / 定时任务
- **增长优化**：增长闭环 / A/B测试 / 历史记录

### 📚 知识中心
- 分类知识库（市场 / 商品 / 内容 / 达人 / 广告 / 案例）
- 知识创建和管理
- 按分类筛选

### ⚙️ 系统设置
- 系统状态监控（MongoDB / Redis / Agent状态）
- 成本控制
- 账号管理
- 平台同步
- 团队管理

---

## 技术栈

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18 | UI框架 |
| Vite | 5 | 构建工具 |
| Tailwind CSS | 3 | 样式系统 |
| ECharts | 6 | 数据可视化 |
| Three.js | — | 3D背景 |

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | — | Web框架 |
| Motor | — | MongoDB异步驱动 |
| PyJWT | — | 认证 |
| passlib | — | 密码哈希 |
| redis-py | — | 缓存 |

### 数据层
| 技术 | 用途 |
|------|------|
| MongoDB | 主数据库 |
| Redis | 缓存和会话 |

### AI/LLM
| 提供商 | 模型 |
|--------|------|
| 通义千问 | qwen-plus |
| DeepSeek | deepseek-chat |
| OpenAI | GPT-4o |
| Mimo | mimo-v2.5-pro |

### 平台对接（MCP Server）
- B站 / 抖音 / 小红书 / 微博

---

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+
- MongoDB 5.0+
- Redis 6.0+

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd EchoFlow-AI

# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

### 配置

```bash
# 编辑后端环境变量
cp backend/.env.example backend/.env
# 配置 MongoDB、Redis、LLM API Key 等
```

### 启动

```bash
# 一键启动（推荐）
./start.sh

# 或分别启动
# 后端
cd backend && uvicorn main:app --host 0.0.0.0 --port 8009 --reload

# 前端
cd frontend && npm run dev -- --port 3009
```

### 访问
- 前端：http://localhost:3009
- 后端 API：http://localhost:8009
- API 文档：http://localhost:8009/docs

### 默认账号
| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

---

## API 端点

### v3.0 企业版 API (`/api/v3`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v3/dashboard` | 企业驾驶舱数据 |
| POST | `/api/v3/coo/dispatch` | AI COO 任务调度 |
| GET | `/api/v3/coo/tasks` | COO 任务列表 |
| GET | `/api/v3/coo/tasks/{id}` | COO 任务详情 |
| POST | `/api/v3/coo/tasks/{id}/execute` | 执行COO任务 |
| POST | `/api/v3/coo/analyze` | AI COO 综合分析 |
| POST | `/api/v3/coo/chat` | AI COO 对话（SSE） |
| GET | `/api/v3/agents` | Agent 列表 |
| GET | `/api/v3/agents/{id}` | Agent 详情 |
| POST | `/api/v3/agents/{id}/execute` | 执行Agent任务 |
| GET | `/api/v3/knowledge` | 知识库列表 |
| POST | `/api/v3/knowledge` | 创建知识条目 |
| GET | `/api/v3/knowledge/categories` | 知识分类 |
| GET | `/api/v3/growth-brain` | 增长大脑数据 |
| GET | `/api/v3/system/status` | 系统状态 |

### v1.x 原有 API（保留兼容）

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/generate` | 标题生成 |
| POST | `/api/optimize` | 标题优化 |
| POST | `/api/trends` | 趋势分析 |
| POST | `/api/script` | 脚本生成 |
| POST | `/api/cover` | 封面生成 |
| POST | `/api/pipeline` | 全流程生产 |
| POST | `/api/strategy` | 策略生成 |
| POST | `/api/growth-loop` | 增长闭环 |
| GET | `/api/hot/{platform}` | 平台热搜 |
| GET | `/api/dashboard` | 数据大屏 |
| ... | 更多 | 见 `/docs` |

---

## 企业每日工作流程

```
上午 9:00 — AI 自动执行
├── 市场分析
├── 竞品更新
├── 商品分析
├── 广告分析
├── 达人分析
├── 热点分析
├── 生成日报
└── 更新 Dashboard

下午 — AI 生成 + 人工审核
├── AI 生成内容
├── AI 生成脚本
├── AI 安排达人
├── AI 生成广告
└── 等待人工审核

晚上 — 数据收集 + 学习
├── 自动收集数据
├── 分析结果
├── 更新知识库
└── 优化策略
```

---

## 项目结构

```
EchoFlow-AI/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── enterprise/          # v3.0 企业版路由
│   │   ├── __init__.py
│   │   └── router.py        # 驾驶舱/COO/Agent/知识 API
│   ├── agents/              # AI Agent 系统
│   │   ├── manager.py       # Agent 编排管理
│   │   ├── topic_agent.py   # 话题 Agent
│   │   ├── trend_agent.py   # 趋势 Agent
│   │   ├── script_agent.py  # 脚本 Agent
│   │   ├── cover_agent.py   # 封面 Agent
│   │   ├── strategy_agent.py # 策略 Agent
│   │   ├── analytics_agent.py # 分析 Agent
│   │   └── memory_agent.py  # 记忆 Agent
│   ├── memory/              # 数据存储层
│   ├── auth/                # 认证系统
│   ├── models/              # 数据模型
│   ├── configs/             # 平台配置
│   └── ...                  # 其他模块
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # 主应用（7页面导航）
│   │   ├── api/client.js    # API 客户端
│   │   ├── components/
│   │   │   ├── EnterpriseDashboard.jsx  # 企业驾驶舱
│   │   │   ├── AICOOPage.jsx           # AI COO 调度中心
│   │   │   ├── AgentsPage.jsx          # 智能体管理
│   │   │   ├── GrowthBrainPage.jsx     # 增长大脑
│   │   │   ├── ToolsPage.jsx           # 工具箱
│   │   │   ├── KnowledgePage.jsx       # 知识中心
│   │   │   ├── SettingsPage.jsx        # 系统设置
│   │   │   ├── LoginPage.jsx           # 登录
│   │   │   └── ...                     # 19个工具组件
│   │   └── index.css        # 样式系统
│   └── tailwind.config.js   # Tailwind 配置
├── start.sh                 # 一键启动脚本
└── README.md
```

---

## 设计理念

> **One Goal → One AI COO → Multiple AI Agents → Continuous Business Growth**

企业只负责制定目标，EchoFlow AI 负责持续实现增长。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0 | 2026-07 | 企业版重构：AI COO + 7 Agent + 驾驶舱 + 增长大脑 |
| v2.2 | — | LLM 模型自由选择 |
| v2.1 | — | 抖音爆款采集浏览器插件、平台数据同步 |
| v2.0 | — | 用户认证、团队管理、成本追踪、AB测试、竞品监控 |
| v1.4 | — | 每日摘要、数据分析面板、定时任务、告警系统 |
| v1.3 | — | 多平台发布、账号管理、数据回流 |
| v1.2 | — | MongoDB + Redis 持久化 |
| v1.1 | — | 策略智能体、增长闭环、四层记忆系统 |
| v1.0 | — | 基础版：标题生成、趋势分析、脚本创作 |

---

## License

MIT
