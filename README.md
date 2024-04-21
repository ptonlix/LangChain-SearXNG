# 🔍 LangChain-SearXNG

简体中文 | [English](<(./README-en.md)>)

<p>
	<p align="center">
		<img height=120 src="./docs/pic/langchain_searxng_log.jpg">
	</p>
	<p align="center">
		<img src="./docs/pic/introduce.jpg"><br>
		<b face="雅黑">基于LangChain和SearXNG打造的开源AI搜索引擎</b>
	<p>
</p>
<p align="center">
<img alt=" Python" src="https://img.shields.io/badge/Python-3.10%2B-blue"/>
<img alt="LangChain" src="https://img.shields.io/badge/LangChain-0.1.16-yellowgreen"/>
<img alt="SearXNG" src="https://img.shields.io/badge/SearXNG-2024.4.10-yellow"/>
<img alt="license" src="https://img.shields.io/badge/license-Apache-lightgrey"/>
</p>

## 🚀 Quick Install

### 1. 部署 SearXNG

> 由于 SearXNG 需要访问外网，建议部署选择外网服务器，以下部署示例选择以腾讯云轻量服务器-Centos 系统为例

根据 [searxng-docker](https://github.com/searxng/searxng-docker)教程，按照以下操作，容器化部署 SearXNG

```shell
# 拉取代码
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker

# 修改域名和录入邮箱
vim .env

# 启动docker
docker compose up
```

### 2. 运行 LangChain-SearXNG

```

```
