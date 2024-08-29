from langchain_community.utilities.searx_search import SearxSearchWrapper
from typing import Optional, List, Any, Dict, Literal
from concurrent.futures import ThreadPoolExecutor
from langchain_searxng.settings.settings import settings
from langchain_searxng.components.searxng.searxng_htmlloader import (
    SearXNGAsyncHtmlLoader,
)
from langchain_community.document_transformers.html2text import Html2TextTransformer
from langchain_searxng.components.searxng.searxng_prompt import (
    SEARCH_TOOLS_TEMPLATE,
    SELECT_BEST_RESULT_TEMPLATE,
)
from langchain.schema.language_model import BaseLanguageModel
from enum import Enum

import httpx
import logging
import asyncio
import json
from langchain_core.tools import tool
from langchain.schema.runnable import (
    ConfigurableField,
    Runnable,
    RunnableLambda,
    RunnableMap,
    RunnablePassthrough,
)
from langchain.prompts import (
    PromptTemplate,
)
from langchain.schema.output_parser import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema.document import Document
from langchain_core.utils.function_calling import convert_to_openai_tool
from operator import itemgetter
from datetime import datetime
import ssl
import re

logger = logging.getLogger(__name__)


class Language(str, Enum):
    ZH_CN = "zh-CN"
    EN_US = "en-US"


class SafeSearch(int, Enum):
    OFF = 0
    MODERATE = 1
    STRICT = 2


class TimeRange(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Category(str, Enum):
    GENERAL = "general"
    IMAGES = "images"
    NEWS = "news"
    MAP = "map"
    MUSIC = "music"
    IT = "it"
    SCIENCE = "science"
    FILES = "files"


@tool
def searxng_search(
    query: str,
    num_results: int,
    language: Optional[
        Literal[
            "zh-CN",
            "en-US",
        ]
    ] = "zh-CN",
    safesearch: Optional[Literal[0, 1, 2]] = None,
    time_range: Optional[
        Literal[
            "",
            "day",
            "week",
            "month",
            "year",
        ]
    ] = None,
    categories: Optional[
        List[
            Literal[
                "general",
                "images",
                "news",
                "map",
                "music",
                "it",
                "science",
                "files",
            ]
        ]
        | Dict
    ] = None,
) -> List[Dict]:
    """
    Search using SearxNG and return only accessible results.

    """

    searxngconfig = settings().searxng
    sswclient = CustomSearxSearchWrapper(searx_host=searxngconfig.host)
    if isinstance(categories, Dict):
        categories = categories.get("Items")  # 适配智谱AI
    logger.info("Searching for relevant urls...")
    result = sswclient.query_searxng_result(
        query=query,
        num_results=num_results,
        language=language,
        safesearch=safesearch,
        time_range=time_range,
        categories=categories,
        engines=searxngconfig.engines,
    )
    logger.info(f"Search num results: {len(result)}")
    return result


def categorized_results(data: Any) -> List[Document]:
    try:
        index_list = data.get("select", [])
        search_result = data.get("search", [])
        if not index_list or not search_result:
            logger.warning("No valid search results or index list found.")
            return []

        results = [search_result[i] for i in index_list if i < len(search_result)]
        logger.info(f"Select Search index: {index_list}  results: {results}")

        accessible_urls = check_urls_access([res["url"] for res in results])
        accessible_results = []
        for res in results:
            if res["url"] in accessible_urls:
                accessible_results.append(res)

        urls_to_look = []
        for res in accessible_results:
            if res.get("url", None):
                urls_to_look.append(res["url"])

        logger.info(f"Accessible Result urls: {urls_to_look}")
        loader = SearXNGAsyncHtmlLoader(
            urls_to_look,
            ignore_load_errors=True,
            verify_ssl=False,
            requests_per_second=3,
            requests_kwargs={"timeout": 5},
        )
        html2text = Html2TextTransformer()

        logger.info("Indexing new urls...")
        docs = loader.load()
        if not docs:
            logger.warning("No documents loaded from URLs.")
            return []

        docs = list(html2text.transform_documents(docs))

        for i in range(len(docs)):
            docs[i].metadata.update(accessible_results[i])

        logger.info(f"Successfully processed {len(docs)} html docs.")
        return docs
    except Exception as e:
        logger.exception(f"Error occurred while retrieving documents: {e}")
        return []


class CustomSearxSearchWrapper(SearxSearchWrapper):

    def query_searxng_result(
        self,
        query: str,
        num_results: int,
        language: Language = Language.ZH_CN,
        safesearch: SafeSearch = None,
        time_range: Optional[TimeRange] = None,
        engines: Optional[List[str]] = None,
        categories: Optional[List[Category]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> List[Dict]:
        """
        Query the SearxNG API and return results.

        Args:
            query (str): The search query.
            num_results (int): Number of results to retrieve.
            language (Language, optional): Language of the search. Defaults to Language.ZH_CN.
            safesearch (SafeSearch, optional): SafeSearch level. Defaults to SafeSearch.MODERATE.
            time_range (Optional[TimeRange], optional): Time range for search. Defaults to TimeRange.YEAR.
            engines (Optional[List[str]], optional): List of engines to use. Defaults to None.
            categories (Optional[List[Category]], optional): List of categories to search. Defaults to None.
            query_suffix (str, optional): Extra suffix for the query. Defaults to "".
            **kwargs (Any): Additional parameters for the API query.

        Returns:
            List[Dict]: List of search results.
        """

        _params = {
            "q": query,
            "language": language,
            "safesearch": safesearch,
        }
        params = {**self.params, **_params, **kwargs}
        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += " " + self.query_suffix
        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += " " + query_suffix
        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)
        if isinstance(categories, list) and len(categories) > 0:
            params["categories"] = ",".join(categories)
        if isinstance(time_range, TimeRange):
            params["time_range"] = time_range
        results = self._searx_api_query(params)
        results = results.results[:num_results]

        if len(results) == 0:
            return [{"Result": "No good Search Result was found"}]

        return results

    async def aquery_searxng_result(
        self,
        query: str,
        num_results: int,
        language: Language = Language.ZH_CN,
        safesearch: SafeSearch = None,
        time_range: Optional[TimeRange] = None,
        engines: Optional[List[str]] = None,
        categories: Optional[List[Category]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> List[Dict]:
        """
        Asynchronously query the SearxNG API and return results.

        Args:
            query (str): The search query.
            num_results (int): Number of results to retrieve.
            language (Language, optional): Language of the search. Defaults to Language.ZH_CN.
            safesearch (SafeSearch, optional): SafeSearch level. Defaults to SafeSearch.MODERATE.
            time_range (Optional[TimeRange], optional): Time range for search. Defaults to TimeRange.YEAR.
            engines (Optional[List[str]], optional): List of engines to use. Defaults to None.
            categories (Optional[List[Category]], optional): List of categories to search. Defaults to None.
            query_suffix (str, optional): Extra suffix for the query. Defaults to "".
            format (str, optional): Format of the response. Defaults to "json".
            **kwargs (Any): Additional parameters for the API query.

        Returns:
            List[Dict]: List of search results.
        """

        _params = {
            "q": query,
            "language": language,
            "safesearch": safesearch,
            "time_range": time_range,
        }
        params = {**self.params, **_params, **kwargs}
        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += " " + self.query_suffix
        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += " " + query_suffix
        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)
        if isinstance(categories, list) and len(categories) > 0:
            params["categories"] = ",".join(categories)
        if isinstance(time_range, TimeRange):
            params["time_range"] = time_range
        results = await self._asearx_api_query(params).results[:num_results]
        if len(results) == 0:
            return [{"Result": "No good Search Result was found"}]

        return results


ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


async def check_url(url: str):
    async with httpx.AsyncClient(verify=ssl_context) as client:
        try:
            response = await client.get(url)
            return url, response.status_code
        except httpx.RequestError:
            return url, None


async def check_urls(urls: list[str]):
    tasks = [check_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    valid_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Error checking URL: {str(result)}")
        else:
            valid_results.append(result)
    return valid_results


def check_urls_access(urls: list[str]) -> list[str]:
    try:
        # Raises RuntimeError if there is no current event loop.
        asyncio.get_running_loop()
        # If there is a current event loop, we need to run the async code
        # in a separate loop, in a separate thread.
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, check_urls(urls))
            results = future.result()
    except RuntimeError:
        results = asyncio.run(check_urls(urls))

    return [url for url, status_code in results if status_code is not None]


def format_result(results: List[Dict]) -> str:
    formatted_docs = []
    formatted_docs_str = ""
    for i, result in enumerate(results):
        content = result.get("content")
        doc_string = f"<doc id='{i}'>{content}</doc>"
        formatted_docs.append(doc_string)
        formatted_docs_str = "\n".join(formatted_docs)
        if len(formatted_docs_str) >= 10000:  # 一次请求不能超过20000字节，减少Token消耗
            logger.info("select formatted_docs is too long.")
            break
    logger.info(f"select formatted_docs length: {len(formatted_docs_str)} done")
    return formatted_docs_str


def extract_numbers_from_text(text) -> list[int]:
    # 使用正则表达式匹配文本中的数字
    numbers = [int(num) for num in re.findall(r"\b\d+\b", text)]
    return numbers


def extract_json_from_content(query: str, content: str) -> Dict:
    """
    从内容中提取JSON字符串并转换为字典。

    Args:
        content (str): 包含JSON的字符串

    Returns:
        Dict: 解析后的JSON字典
    """
    # 使用正则表达式匹配JSON部分
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        json_str = match.group()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.error(f"无法解析JSON: {json_str}")
    logger.warning(f"未找到有效的JSON: {content}")
    return {
        "query": query,
        "num_results": 30,
        "language": "zh-CN",
        "safesearch": 1,
        "categories": ["general"],
    }


def process_llm_response(x: dict):
    """
    处理语言模型的响应。

    Args:
        x: 语言模型的响应对象

    Returns:
        Dict: 处理后的参数字典
    """
    query = x.get("query")
    output = x.get("output")
    if output.tool_calls:
        return output.tool_calls[0]["args"]
    return extract_json_from_content(query, output.content)


def create_seaxng_retriever_v2(llm: BaseLanguageModel) -> Runnable:
    SEARCH_TOOLS_PROMPT = PromptTemplate.from_template(SEARCH_TOOLS_TEMPLATE).partial(
        current_date=datetime.now().isoformat()
    )
    SELECT_BEST_RESULT_PROMPT = PromptTemplate.from_template(
        SELECT_BEST_RESULT_TEMPLATE
    ).partial(current_date=datetime.now().isoformat())

    llm_with_tools = llm.bind(tools=[convert_to_openai_tool(searxng_search)])

    _search = (
        RunnableMap(
            {
                "query": RunnablePassthrough(),
                "output": SEARCH_TOOLS_PROMPT | llm_with_tools,
            }
        )
        | process_llm_response
        | searxng_search
    ).with_config(run_name="SearXNGSearchResult")

    _select = (
        {
            "query": RunnableLambda(itemgetter("query")),
            "context": RunnableLambda(itemgetter("context")),
        }
        | SELECT_BEST_RESULT_PROMPT
        | llm
        | StrOutputParser()
        | extract_numbers_from_text
    )

    chain = (
        {"query": RunnablePassthrough(), "search": _search}
        | RunnableMap(
            {
                "select": RunnableMap(
                    {
                        "context": RunnableLambda(itemgetter("search"))
                        | RunnableLambda(format_result),
                        "query": RunnableLambda(itemgetter("query")),
                    }
                )
                | _select,
                "search": RunnableLambda(itemgetter("search")),
            }
        )
        | categorized_results
    )

    return chain.configurable_alternatives(
        # This gives this field an id
        # When configuring the end runnable, we can then use this id to configure this field
        ConfigurableField(id="retriever"),
        default_key="searx",
    ).with_config(run_name="FinalSourceRetriever")


if __name__ == "__main__":

    import pprint
    from langchain_openai import ChatOpenAI

    print(searxng_search.name)
    print(searxng_search.description)
    print(searxng_search.args)

    TEST_QUESTION_PROMPT = PromptTemplate.from_template(SEARCH_TOOLS_TEMPLATE).partial(
        current_date=datetime.now().isoformat()
    )
    SELECT_BEST_RESULT_PROMPT = PromptTemplate.from_template(
        SELECT_BEST_RESULT_TEMPLATE
    ).partial(current_date=datetime.now().isoformat())

    openai_settings = settings().openai
    zhipuai_settings = settings().zhipuai
    # llm = ChatOpenAI(
    #     temperature=0,
    #     model_name=openai_settings.modelname,
    #     api_key=openai_settings.api_key,
    #     openai_api_base=openai_settings.api_base,
    # )
    llm = ChatOpenAI(
        temperature=zhipuai_settings.temperature,
        model_name=zhipuai_settings.modelname,
        api_key=zhipuai_settings.api_key,
        openai_api_base="https://open.bigmodel.cn/api/paas/v4/",
    )

    llm_with_tools = llm.bind_tools([searxng_search])

    _search = (
        RunnablePassthrough()
        | TEST_QUESTION_PROMPT
        | llm_with_tools
        | (lambda x: x.tool_calls[0]["args"])
        | searxng_search
    ).with_config(run_name="SearXNGSearchResult")

    _select = (
        {
            "query": RunnableLambda(itemgetter("query")),
            "context": RunnableLambda(itemgetter("context")),
        }
        | SELECT_BEST_RESULT_PROMPT
        | llm
        | JsonOutputParser()
    )

    chain = (
        {"query": RunnablePassthrough(), "search": _search}
        | RunnableMap(
            {
                "select": RunnableMap(
                    {
                        "context": RunnableLambda(itemgetter("search"))
                        | RunnableLambda(format_result),
                        "query": RunnableLambda(itemgetter("query")),
                    }
                )
                | _select,
                "search": RunnableLambda(itemgetter("search")),
            }
        )
        | RunnableLambda(categorized_results)
    )
    msg = chain.invoke("中国旅游有哪些好玩的地点")

    pprint.pp(msg)
