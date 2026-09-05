#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

echo ""
echo -e "${BOLD}${CYAN} ╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN} ║       国关推演平台  IR Intelligence Platform          ║${NC}"
echo -e "${BOLD}${CYAN} ║              一键启动脚本 v2.1                        ║${NC}"
echo -e "${BOLD}${CYAN} ╚══════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BOLD}[1/7] 检查 Python 环境...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED} ✗ 未找到 python3，请安装 Python 3.10+${NC}"; exit 1
fi
PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN} ✓ Python ${PY_VER}${NC}"

echo -e "${BOLD}[2/7] 检查 Node.js 环境...${NC}"
if ! command -v node &>/dev/null; then
    echo -e "${RED} ✗ 未找到 node，请安装 Node.js 18+${NC}"; exit 1
fi
echo -e "${GREEN} ✓ Node.js $(node --version)${NC}"

echo -e "${BOLD}[3/7] 检查配置文件...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW} ⚠ 已创建 .env，请填写 ANTHROPIC_API_KEY 后重新运行${NC}"
        exit 0
    else
        echo -e "${RED} ✗ 未找到 .env 文件${NC}"; exit 1
    fi
fi
if grep -q 'ANTHROPIC_API_KEY=sk-' .env 2>/dev/null; then
    echo -e "${GREEN} ✓ .env 配置就绪${NC}"
else
    echo -e "${YELLOW} ⚠ 未检测到有效的 ANTHROPIC_API_KEY，AI 功能不可用${NC}"
fi

echo -e "${BOLD}[4/7] 检查 Python 依赖...${NC}"
if ! python3 -c "import fastapi, sqlalchemy, anthropic, uvicorn, slowapi, jwt, passlib, feedparser, pydantic_settings, reportlab, geopy" &>/dev/null; then
    echo " → 安装 Python 依赖..."
    python3 -m pip install -r backend/requirements.txt -q
    echo -e "${GREEN} ✓ 依赖安装完成${NC}"
else
    echo -e "${GREEN} ✓ Python 依赖就绪${NC}"
fi

echo -e "${BOLD}[5/7] 数据库迁移...${NC}"
if [ -f "alembic.ini" ]; then
    if python3 -m alembic upgrade head 2>/dev/null; then
        echo -e "${GREEN} ✓ 数据库已是最新${NC}"
    else
        echo -e "${YELLOW} ⚠ alembic 迁移异常，尝试 create_all 回退...${NC}"
        python3 -c "from backend.db.database import create_all_tables; create_all_tables()" 2>/dev/null \
          && echo -e "${GREEN} ✓ 数据库表已创建${NC}" \
          || echo -e "${YELLOW} ⚠ 数据库初始化警告（继续）${NC}"
    fi
fi

echo -e "${BOLD}[6/7] 检查前端依赖...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo " → 安装前端依赖..."
    (cd frontend && npm ci --silent)
    echo -e "${GREEN} ✓ 前端依赖安装完成${NC}"
else
    echo -e "${GREEN} ✓ 前端依赖就绪${NC}"
fi

echo -e "${BOLD}[7/7] 检查端口占用...${NC}"
check_port() {
    if lsof -i ":$1" &>/dev/null; then
        echo -e "${YELLOW} ⚠ 端口 $1 已被占用，将尝试释放${NC}"
        lsof -ti ":$1" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}
check_port 8000
check_port 5173
echo -e "${GREEN} ✓ 端口检查完成${NC}"

echo ""
echo " 启动服务中..."

python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend --log-level warning &
BACKEND_PID=$!
echo " → 后端 PID: $BACKEND_PID"

echo " → 等待后端就绪..."
for i in $(seq 1 40); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health',timeout=2)" &>/dev/null; then
        echo -e "${GREEN} ✓ 后端已就绪${NC}"
        break
    fi
    sleep 1
done

(cd frontend && npm run dev) &
FRONTEND_PID=$!
echo " → 前端 PID: $FRONTEND_PID"

sleep 3

if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:5173" &>/dev/null &
elif command -v open &>/dev/null; then
    open "http://localhost:5173" &>/dev/null &
fi

echo ""
echo -e "${BOLD}${GREEN} ╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN} ║  ✓  平台已成功启动！                                 ║${NC}"
echo -e "${BOLD}${GREEN} ╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}${GREEN} ║  前端界面:   http://localhost:5173                   ║${NC}"
echo -e "${BOLD}${GREEN} ║  后端 API:   http://localhost:8000                   ║${NC}"
echo -e "${BOLD}${GREEN} ║  API 文档:   http://localhost:8000/api/docs          ║${NC}"
echo -e "${BOLD}${GREEN} ╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}${GREEN} ║  按 Ctrl+C 停止所有服务                              ║${NC}"
echo -e "${BOLD}${GREEN} ╚══════════════════════════════════════════════════════╝${NC}"
echo ""

cleanup() {
    echo ""
    echo " 正在停止服务..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo " 已停止"
    exit 0
}
trap cleanup INT TERM
wait
