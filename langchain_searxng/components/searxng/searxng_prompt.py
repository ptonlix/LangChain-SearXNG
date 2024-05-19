SEARCH_TOOLS_TEMPLATE = """\
searxng_search的工具参数如下：
Args:
    query (str): The search query.
    num_results (int): Number of results to retrieve.
    language (Optional[str]): Language of the search. Defaults to "zh-CN".
    safesearch (Optional[int]): SafeSearch level. Defaults to None.
        - 0: Disable SafeSearch.
        - 1: Moderate SafeSearch.
        - 2: Strict SafeSearch.
    time_range (Optional[str]): Time range for search. Defaults to None.
        - "day": Results from the past day.
        - "week": Results from the past week.
        - "month": Results from the past month.
        - "year": Results from the past year.
    categories (Optional[List[str]]): List of categories to search. Defaults to None.
        Possible values:
        - "general": General search results.
        - "images": Image search results.
        - "news": News search results.
        - "map": Map search results.
        - "music": Music search results.
        - "it": IT-related search results.
        - "science": Science-related search results.
        - "files": File search results.

searxng_search工具调用例子：
```
searxng_search(query="LangChain是什么", num_results=30, language="zh-CN", safesearch=1,  time_range="year", categories=['general', 'images', 'news'])
```
请学习searxng_search参数含义,选择最合适回答以下问题的searxng_search工具的参数
```
{query}
```
要求
1. num_results必须大于20个,不能超过30个
2. safesearch根据问题性质选择
3. time_range根据问题的实效性要求进行选择, 不输入表示不限时间
4. categories根据问题的所属分类选择，允许多选
5. 请严格满足searxng_search输入参数要求

必须只返回一个工具调用即可
当前时间:{current_date}


"""

SELECT_BEST_RESULT_TEMPLATE = """\
以下是根据问题搜索出来结果：
<context>
    {context}
<context/>
请从上面搜索结果列表中, 选择与以下问题最匹配的搜索结果
{query}
当前时间:{current_date}
要求:
1.请按照返回格式要求,返回搜索结果ID列表,ID个数不能超过6个
2.搜索结果ID一定不能虚构,从搜索结果列表ID中选取

返回数据格式举例：
[1, 2, 3, 4, 5]
"""
