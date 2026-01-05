# 使用 Python 3.10 基础镜像
FROM python:3.10-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    tzdata \
    curl \
    wget \
    iputils-ping \
    net-tools \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# ============================================================================
# 【重要修复】使用多个镜像源，提高成功率
# ============================================================================
# 方案 1: 优先使用阿里云镜像（更稳定）
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 如果上面失败，使用这个版本（带自动切换）：
# RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ \
#     || pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
#     || pip install --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple \
#     || pip install --no-cache-dir -r requirements.txt

# 复制所有应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /data/models

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 启动命令
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.runOnSave=false"]