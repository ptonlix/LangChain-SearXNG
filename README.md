# 🔍 LangChain-SearXNG

简体中文 | [English](<(./README-en.md)>)

<p>
	<p align="center">
		<img height=120 src="./docs/pic/langchain_searxng_log.jpg">
	</p>
	<p align="center">
		<img height=50 src="./docs/pic/introduce.jpg"><br>
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

> 由于 SearXNG 需要访问外网，建议部署选择外网服务器  
> 以下部署示例选择以腾讯云轻量服务器-Centos 系统为例

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

### 2.部署 Python 环境

- 安装 miniconda

```shell
mkdir ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash
```

- 创建虚拟环境

```shell
# 创建环境
conda create -n DeepRead python==3.10.11
```

- 安装 poetry

```shell
# 安装
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. 运行 LangChain-SearXNG

```shell
# 克隆项目代码到本地
git clone https://github.com/ptonlix/LangChain-SearXNG.git
conda activate LangChain-SearXNG # 激活环境
cd LangChain-SearXNG # 进入项目
poetry install # 安装依赖

# 启动项目
python -m langchain_searxng
```

### 4.查看 API

访问: http://localhost:8002/docs 获取 API 信息
