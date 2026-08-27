#!/bin/bash
# EchoFlow AI 一键启动/关闭脚本
# 用法:
#   ./start.sh          启动前后端
#   ./start.sh stop     关闭前后端

set -e

CONDA_ENV="/opt/anaconda3/envs/shopping_agent"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PIDFILE="/tmp/echowflow.pids"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── 关闭 ──────────────────────────────────────────────────
stop() {
    echo -e "${YELLOW}⏹ 正在停止 EchoFlow AI...${NC}"

    # 从 pid 文件读取
    if [ -f "$PIDFILE" ]; then
        while read pid; do
            kill "$pid" 2>/dev/null && echo -e "  停止 PID $pid"
        done < "$PIDFILE"
        rm -f "$PIDFILE"
    fi

    # 兜底: 按端口杀进程
    for port in 8009 3009; do
        pid=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$pid" ]; then
            kill $pid 2>/dev/null
            echo -e "  停止 :$port (PID $pid)"
        fi
    done

    echo -e "${GREEN}✅ EchoFlow AI 已停止${NC}"
}

# 支持 ./start.sh stop
if [ "$1" = "stop" ]; then
    stop
    exit 0
fi

# ── 清理残留 ──────────────────────────────────────────────
stop 2>/dev/null || true
sleep 1

# ── 检查依赖 ──────────────────────────────────────────────
echo -e "${CYAN}🔍 检查基础服务...${NC}"
redis-cli ping >/dev/null 2>&1 || { echo -e "${RED}❌ Redis 未运行，请先: brew services start redis${NC}"; exit 1; }
mongosh --eval "db.runCommand({ping:1})" --quiet >/dev/null 2>&1 || { echo -e "${RED}❌ MongoDB 未运行，请先: brew services start mongodb-community${NC}"; exit 1; }
echo -e "${GREEN}  ✓ MongoDB & Redis 正常${NC}"

# ── 启动后端 ──────────────────────────────────────────────
echo -e "${CYAN}🚀 启动后端 (FastAPI :8009)...${NC}"
cd "$BACKEND_DIR"
PYTHONPATH="$BACKEND_DIR" SMART_COLLECTION_USE_LLM=false "$CONDA_ENV/bin/python" -m uvicorn main:app --host 0.0.0.0 --port 8009 &
BACKEND_PID=$!

for i in $(seq 1 15); do
    curl -s http://127.0.0.1:8009/docs -o /dev/null 2>/dev/null && break
    sleep 1
done
echo -e "${GREEN}  ✓ 后端已启动 (PID $BACKEND_PID)${NC}"

# ── 启动前端 ──────────────────────────────────────────────
echo -e "${CYAN}🚀 启动前端 (Vite :3009)...${NC}"
cd "$FRONTEND_DIR"
export PATH="$CONDA_ENV/bin:$PATH"
npx vite --port 3009 &
FRONTEND_PID=$!

sleep 3

# 保存 PID
echo "$BACKEND_PID" > "$PIDFILE"
echo "$FRONTEND_PID" >> "$PIDFILE"

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ EchoFlow AI 已启动${NC}"
echo -e "${GREEN}  🌐 前端: http://localhost:3009${NC}"
echo -e "${GREEN}  📡 后端: http://localhost:8009${NC}"
echo -e "${GREEN}  📚 API:  http://localhost:8009/docs${NC}"
echo -e "${GREEN}────────────────────────────────────────${NC}"
echo -e "${GREEN}  ⏹ 停止:  ./start.sh stop${NC}"
echo -e "${GREEN}  ⏹ 或:    Ctrl+C${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

cleanup() {
    stop
    exit 0
}
trap cleanup SIGINT SIGTERM

wait
