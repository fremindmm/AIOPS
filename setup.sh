#!/bin/bash

# AIOPS 快速启动脚本
# Quick setup script for AIOPS

echo "======================================"
echo "   AIOPS 智能运维平台 - 环境配置"
echo "======================================"

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 版本过低，需要 3.8 或更高版本"
    echo "   当前版本: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python 版本检查通过: $PYTHON_VERSION"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "📦 升级 pip..."
pip install --upgrade pip -q

# 安装依赖
echo "📦 安装生产环境依赖..."
pip install -r requirements.txt -q

# 询问是否安装开发依赖
read -p "是否安装开发环境依赖? (y/N): " install_dev
if [[ $install_dev =~ ^[Yy]$ ]]; then
    echo "📦 安装开发环境依赖..."
    pip install -r requirements-dev.txt -q
fi

# 检查端口
PORT=5001
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $PORT 已被占用"
    read -p "请输入新的端口号 (默认: 5002): " NEW_PORT
    PORT=${NEW_PORT:-5002}
    # 更新 app.py 中的端口
    sed -i.bak "s/port=5001/port=$PORT/g" app.py
    sed -i.bak "s/localhost:5001/localhost:$PORT/g" app.py
fi

echo ""
echo "======================================"
echo "✅ 环境配置完成!"
echo "======================================"
echo ""
echo "🚀 启动命令:"
echo "   python app.py"
echo ""
echo "🌐 访问地址:"
echo "   http://localhost:$PORT"
echo ""
echo "📚 查看文档:"
echo "   cat README.md"
echo ""
echo "🤝 贡献指南:"
echo "   cat CONTRIBUTING.md"
echo ""

# 询问是否立即启动
read -p "是否立即启动服务? (Y/n): " start_now
if [[ ! $start_now =~ ^[Nn]$ ]]; then
    echo "🚀 启动 AIOPS 服务..."
    python app.py
fi