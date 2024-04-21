import logging

from injector import inject
from langchain_searxng.settings.settings import Settings, SearXNGSettings
from langchain_community.utilities.searx_search import SearxSearchWrapper
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema.retriever import BaseRetriever
from langchain.schema.document import Document
from langchain_community.document_loaders.async_html import AsyncHtmlLoader
from langchain_community.document_transformers.html2text import Html2TextTransformer
from requests.exceptions import RequestException
from pydantic import BaseModel
from typing import List, Optional

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


class SearXNGRetriever(BaseRetriever):
    search: SearxSearchWrapper
    searxng: SearXNGSettings
    docsource_list: List[DocSource] = []

    def get_docsource_list(self) -> List[DocSource]:
        return self.docsource_list

    def clear_docsource_list(self):
        self.docsource_list = []

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
            loader = AsyncHtmlLoader(urls_to_look)
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
        except (RequestException, IndexError, KeyError) as e:
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
