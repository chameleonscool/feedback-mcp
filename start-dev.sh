#!/bin/bash
# User Intent MCP 开发模式启动脚本
# 同时启动后端和前端开发服务器

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 User Intent MCP 开发模式${NC}"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Python 虚拟环境
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ 发现 Python 虚拟环境${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠ 未找到虚拟环境，使用系统 Python${NC}"
fi

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}🛑 停止服务...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# 启动后端
echo -e "\n${GREEN}🔧 启动后端服务...${NC}"
cd src
PYTHONPATH=. python -m uvicorn web_multi_tenant:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 2

# 启动前端
if [ -d "frontend" ]; then
    echo -e "${GREEN}🎨 启动前端开发服务器...${NC}"
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        npm install
    fi
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

echo ""
echo -e "${GREEN}✅ 服务已启动${NC}"
echo -e "   后端: http://localhost:8000"
echo -e "   前端: http://localhost:5173"
echo -e "   管理后台: http://localhost:8000/admin"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo ""

# 等待进程
wait
