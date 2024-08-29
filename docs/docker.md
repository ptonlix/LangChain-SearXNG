## 构建镜像

docker build -t langchain-searxng:v0.1.8 .

## 运行容器

docker run -p 8002:8002 -p 8501:8501 \
 -v ./settings-pro.yaml:/app/config/settings.yaml \
 --name langchain-searxng \
langchain-searxng:v0.1.8
