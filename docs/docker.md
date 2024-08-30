## 构建镜像

```shell
docker build -t langchain-searxng:v0.1.8 .
```

## 运行容器

```shell
docker run -p 8002:8002 -p 8501:8501 \
 -v ./settings-pro.yaml:/app/config/settings.yaml \
 --name langchain-searxng \
langchain-searxng:v0.1.8
```

## 推送新镜像

```shell
docker tag langchain-searxng:v0.1.8 ptonlix/langchain-searxng:v0.1.8
docker push ptonlix/langchain-searxng:v0.1.8

docker tag ptonlix/langchain-searxng:v0.1.8 ptonlix/langchain-searxng:latest
docker push ptonlix/langchain-searxng:latest
```
