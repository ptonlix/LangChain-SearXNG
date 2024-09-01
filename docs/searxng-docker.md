## 单独部署 Searxng-docker

### 1. 部署 SearXNG

> 由于 SearXNG 需要访问外网，建议部署选择外网服务器  
> 以下部署示例选择以腾讯云轻量服务器-Centos 系统为例

根据 [searxng-docker](https://github.com/searxng/searxng-docker)教程，按照以下操作，容器化部署 SearXNG

```shell
# 拉取代码
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker

# 修改域名和录入邮箱
vim .env

# 修改searxng配置文件 searxng/settings.yml
# 注意修改 limiter 和search，其它参数保持原配置文件不变
# see https://docs.searxng.org/admin/settings/settings.html#settings-use-default-settings
use_default_settings: true
server:
  limiter: false  # can be disabled for a private instance
search:
  formats:
    - html
    - json

# 启动docker
docker compose up
```
