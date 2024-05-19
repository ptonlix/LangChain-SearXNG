import logging

from injector import inject
from langchain_searxng.settings.settings import Settings, SearXNGSettings
from langchain_searxng.components.searxng.searxng_custom import (
    create_seaxng_retriever_v2,
)
from langchain_community.utilities.searx_search import SearxSearchWrapper
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema.retriever import BaseRetriever
from langchain.schema.document import Document
from langchain_community.document_loaders.async_html import AsyncHtmlLoader
from langchain_community.document_transformers.html2text import Html2TextTransformer
from pydantic import BaseModel
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio
import httpx

logger = logging.getLogger(__name__)


class DocSource(BaseModel):
    title: Optional[str]
    source_link: str
    description: Optional[str]


class SearXNGComponent:

    @inject
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.searxng = settings.searxng
        self.search_retriever = SearXNGRetriever(
            search=SearxSearchWrapper(searx_host=self.searxng.host),
            searxng=self.searxng,
        )
        self.search_retriever_v2 = create_seaxng_retriever_v2


class SearXNGRetriever(BaseRetriever):
    search: SearxSearchWrapper
    searxng: SearXNGSettings
    docsource_list: List[DocSource] = []

    def get_docsource_list(self) -> List[DocSource]:
        return self.docsource_list

    def clear_docsource_list(self):
        self.docsource_list = []

    async def check_url(self, url: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                return url, response.status_code
            except httpx.RequestError:
                return url, None

    async def check_urls(self, urls: list[str]):
        tasks = [self.check_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        for url, status_code in results:
            if status_code is None:
                logger.warning(f"URL: {url} - Failed to connect")
        return results

    def check_urls_access(self, urls: list[str]) -> list[str]:
        try:
            # Raises RuntimeError if there is no current event loop.
            asyncio.get_running_loop()
            # If there is a current event loop, we need to run the async code
            # in a separate loop, in a separate thread.
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, self.check_urls(urls))
                results = future.result()
        except RuntimeError:
            results = asyncio.run(self.check_urls(urls))

        return [url for url, status_code in results if status_code is not None]

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        try:
            # Get search questions
            logger.info("Generating questions for Searx Search ...")
            # Get urls
            logger.info("Searching for relevant urls...")
            urls_to_look = []
            search_results = self.search.results(
                query,
                language=self.searxng.language,
                safesearch=self.searxng.safesearch,
                categories=self.searxng.categories,
                engines=self.searxng.engines,
                num_results=self.searxng.num_results,
            )
            logger.info("Searching for relevant urls...")
            logger.info(f"Search results: {search_results}")
            for res in search_results:
                if res.get("link", None):
                    urls_to_look.append(res["link"])

            logger.info(f"Result urls: {urls_to_look}")
            urls_to_look = self.check_urls_access(
                urls_to_look
            )  # 检查是否能正常访问这些urls
            loader = AsyncHtmlLoader(
                urls_to_look,
                ignore_load_errors=True,
            )
            html2text = Html2TextTransformer()
            logger.info("Indexing new urls...")
            docs = loader.load()
            docs = list(html2text.transform_documents(docs))
            for i in range(len(docs)):
                if search_results[i].get("title", None):
                    docs[i].metadata["title"] = search_results[i]["title"]
                self.docsource_list.append(
                    DocSource(
                        title=docs[i].metadata.get("title"),
                        source_link=docs[i].metadata.get("source"),
                        description=docs[i].metadata.get("description"),
                    )
                )

            logger.info("Get html docs done...")
            return docs
        except Exception as e:
            logger.error(f"Error occurred while retrieving documents: {e}")
            return []


if __name__ == "__main__":
    from langchain_searxng.di import global_injector
    import uuid

    s = SearXNGComponent(global_injector.get(Settings))

    docs = s.search_retriever._get_relevant_documents(
        "中国有多大？",
        run_manager=CallbackManagerForRetrieverRun(
            run_id=uuid.uuid4(), handlers=[], inheritable_handlers=[]
        ),
    )

    # print(docs)

    print(s.search_retriever.get_docsource_list())
