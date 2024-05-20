## AI+Searxng v1 版本工作流

<p align="center">
	<img height=300 src="./pic/yuanli.png"><br>
  <b face="雅黑">AI+SearXNG v1版本工作流</b>
</p>

目前 LLM Agent 本质上都是使用了 Prompt+Tool 两个方面的能力
以我们 AI 搜索引擎 Agent 为例：

1. 将根据用户搜索关键词，去调用 Tool 收集信息
2. 将收集到的信息通过与 system prompt 等提示词组合，输入到大模型
3. 大模型将依据收集到的上下文，提供更符合用户要求的搜索答案
