#!/bin/bash
# User Intent MCP 一键启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 默认端口
PORT="${USERINTENT_WEB_PORT:-8788}"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT    指定端口 (默认: 8788)"
            echo "  --rebuild      重新构建前端"
            echo "  -h, --help     显示帮助信息"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

echo -e "${GREEN}🚀 User Intent MCP 启动脚本${NC}"
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

# 检查依赖
echo -e "\n${GREEN}📦 检查依赖...${NC}"
pip install -q -e . 2>/dev/null || true
pip install -q lark_oapi 2>/dev/null || true

# 构建前端（如果存在且需要）
if [ -d "frontend" ]; then
    if [ ! -d "frontend/dist" ] || [ "$REBUILD" == "true" ]; then
        echo -e "\n${GREEN}🔨 构建前端...${NC}"
        cd frontend
        if [ ! -d "node_modules" ]; then
            echo "安装前端依赖..."
            npm install --silent
        fi
        npm run build --silent
        cd ..
        echo -e "${GREEN}✓ 前端构建完成${NC}"
    else
        echo -e "${GREEN}✓ 前端已构建 (使用 --rebuild 重新构建)${NC}"
    fi
fi

# 启动后端服务
echo -e "\n${GREEN}🌐 启动服务...${NC}"
echo -e "   后端: http://localhost:${PORT}"
echo -e "   React 前端: http://localhost:${PORT}/app"
echo -e "   管理后台: http://localhost:${PORT}/admin"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
echo ""

cd src
PYTHONPATH=. python -m uvicorn web_multi_tenant:app --host 0.0.0.0 --port "$PORT"
