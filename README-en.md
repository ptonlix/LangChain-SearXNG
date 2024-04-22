# 🔍 LangChain-SearXNG

[简体中文](./README.md) | English

<p>
	<p align="center">
		<img height=120 src="./docs/pic/langchain_searxng_log.jpg">
	</p>
	<p align="center">
		<img height=50 src="./docs/pic/introduce.jpg"><br>
		<b face="雅黑">An open-source AI search engine based on LangChain and SearXNG</b>
	<p>
</p>
<p align="center">
<img alt=" Python" src="https://img.shields.io/badge/Python-3.10%2B-blue"/>
<img alt="LangChain" src="https://img.shields.io/badge/LangChain-0.1.16-yellowgreen"/>
<img alt="SearXNG" src="https://img.shields.io/badge/SearXNG-2024.4.10-yellow"/>
<img alt="license" src="https://img.shields.io/badge/license-Apache-lightgrey"/>
</p>

## 🚀 Quick Install

### 1. Deploy SearXNG

> As SearXNG needs access to the Internet, it is recommended to deploy it on a server with Internet access.  
> The following deployment example uses Tencent Cloud's lightweight server with CentOS system.

Follow the steps below to containerize and deploy SearXNG according to the [searxng-docker](https://github.com/searxng/searxng-docker) tutorial.

```shell
# Clone the code
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker

# Modify the domain name and enter the email address
vim .env

# Start docker
docker compose up
```

### 2. Deploy Python Environment

- Install miniconda

```shell
mkdir ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash
```

- Create a virtual environment

```shell
# Create the environment
conda create -n DeepRead python==3.10.11
```

- Install poetry

```shell
# Install
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Run LangChain-SearXNG

- Install dependencies

```shell
# Clone the project code to local
git clone https://github.com/ptonlix/LangChain-SearXNG.git
conda activate LangChain-SearXNG # Activate the environment
cd LangChain-SearXNG # Enter the project directory
poetry install # Install dependencies
```

- Modify the configuration file

[OpenAI 文档](https://platform.openai.com/docs/introduction)  
[ZhipuAI 文档](https://open.bigmodel.cn/dev/howuse/introduction)  
[LangChain API](https://smith.langchain.com)

```shell
# settings.yaml

Enter the following variables in the configuration file or set them via environment variables:

# OPENAI Large Model API
OPENAI_API_BASE
OPENAI_API_KEY

# ZHIPUAI Zhishang API
ZHIPUAI_API_KEY

# LangChain Debugging API
LANGCHAIN_API_KEY

# SearXNG request address
SEARX_HOST
```
