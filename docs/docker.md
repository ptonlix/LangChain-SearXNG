## 构建镜像

docker build -t langchain-searxng .

## 运行容器

docker run -p 8002:8002 -p 8501:8501 langchain-searxng
