## 配置文件说明

- V1 标识 只有使用 v1 版本搜索接口才使用
- V2 标识 只有使用 v2 版本搜索接口才使用
- 未标识表示则表示公用

```yaml
# 服务器配置
server:
  env_name: ${APP_ENV:prod}
  port: ${PORT:8002}
  cors:
    enabled: false
    allow_origins: ["*"]
    allow_methods: ["*"]
    allow_headers: ["*"]
  auth:
    enabled: true #是否开启认证
    secret: "Basic c2VjcmV0OmtleQ==" # Http Authorization认证

# 大模型配置
# 选项有4个 "openai", "zhipuai", "zhipuwebsearch", "all", "mock"
# all表示同时支持3️个模型，根据API传入参数决定使用哪个大模型
# zhipuwebsearch 为智谱搜索定制模型
llm:
  mode: all

# 向量模型
# 选项有3个 openai zhipuai mock
# 国内环境建议选择zhipuai比较稳定
# V1版本
embedding:
  mode: zhipuai

# openai模型参数
openai:
  temperature: 1
  modelname: "gpt-3.5-turbo-0125"
  api_base: ${OPENAI_API_BASE:}
  api_key: ${OPENAI_API_KEY:}

# deepseek模型参数
deepseek:
  temperature: 1
  modelname: "deepseek-chat"
  api_base: ${DEEPSPEAK_API_BASE:}
  api_key: ${DEEPSPEAK_API_KEY:}

# zhipuai模型参数
zhipuai:
  temperature: 0.95
  top_p: 0.6
  modelname: "glm-3-turbo"
  api_key: ${ZHIPUAI_API_KEY:}
  api_base: ${ZHIPUAI_API_BASE:}

# LangSmith调试参数
# 详情见 https://smith.langchain.com
langsmith:
  trace_version_v2: true
  api_key: ${LANGCHAIN_API_KEY:}

# SearXNG参数
# 详情见 https://docs.searxng.org
searxng:
  host: ${SEARX_HOST:} # SearXNG请求地址
  language: "zh-CN" #搜索语言 英文 en-US # V1版本
  safesearch: 1 #搜索安全级别,内容过滤 0无限制 1为中级 2严格 # V1版本
  categories: "general" #搜索分类 [ general images videos news map music it science files social media] # V1版本
  engines: ["bing", "brave", "duckduckgo"] # 搜索引擎 google、yahoo 等
  num_results: 3 # 搜索结果个数 # V1版本
```

## 私有配置文件

由于配置文件涉及一些 API KEY 等隐私信息，在不改动默认配置文件的情况下，可以新增一个单独的私有配置文件，进行加载

详情见 `langchain_searxng/settings` 代码

```shell
# 1. 设置环境变量
export LS_PROFILES=pro

# 2. 新增配置文件
vim settings-pro.yaml

# 3. 复制默认配置文件，增加API_KEY等信息

# 4. 启动项目，程序会自动合并两个配置文件，冲突地方以settings-pro.yaml为准

```

## 动态加载配置文件

通过监听 yaml 配置文件发生内容变化，程序会重新加载文件，方便实时调整参数

详情见 `langchain_searxng/__main__.py` 代码
