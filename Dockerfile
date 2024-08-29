# 使用阿里云的Python 3.10镜像作为基础镜像
FROM python:3.10.11

# 设置工作目录
WORKDIR /app

# 安装 Poetry
RUN pip install poetry -i https://pypi.tuna.tsinghua.edu.cn/simple

# 将 Poetry 添加到 PATH
ENV PATH="/root/.local/bin:$PATH"

# 复制项目文件
COPY . /app

# 创建config目录
RUN mkdir -p /app/config

# 安装项目依赖
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# 暴露端口
EXPOSE 8002 8501

# 创建启动脚本
RUN echo '#!/bin/bash\n\
    if [ -f /app/config/settings.yaml ]; then\n\
    cp /app/config/settings.yaml /app/settings.yaml\n\
    echo "Using outside existing settings.yaml in /app"\n\
    elif [ -f /app/settings.yaml ]; then\n\
    echo "Using existing settings.yaml in /app"\n\
    else\n\
    echo "No settings.yaml found. Using default configuration."\n\
    fi\n\
    python -m langchain_searxng &\n\
    cd webui && streamlit run webui.py\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# 设置启动命令
CMD ["/app/start.sh"]