import logging

from injector import inject, singleton
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings, DeterministicFakeEmbedding

from langchain_searxng.settings.settings import Settings
from langchain_searxng.components.embedding.custom.zhipuai import ZhipuaiTextEmbeddings


logger = logging.getLogger(__name__)


class EmbeddingComponent:
    @inject
    def __init__(self, settings: Settings) -> None:
        embedding_mode = settings.embedding.mode
        logger.info("Initializing the embedding in mode=%s", embedding_mode)
        match embedding_mode:
            case "local":
                ...  # Todo
            case "openai":
                openai_settings = settings.openai
                self._embedding = OpenAIEmbeddings(
                    api_key=openai_settings.api_key,
                    openai_api_base=openai_settings.api_base,
                )
            case "zhipuai":
                zhipuai_settings = settings.zhipuai
                self._embedding = ZhipuaiTextEmbeddings(
                    zhipuai_api_key=zhipuai_settings.api_key
                )
            case "mock":
                self._embedding = DeterministicFakeEmbedding(size=1352)

    @property
    def embedding(self) -> Embeddings:
        return self._embedding

    @property
    def total_tokens(self) -> int:
        try:
            return self._embedding.count_token
        except Exception:
            return 0
