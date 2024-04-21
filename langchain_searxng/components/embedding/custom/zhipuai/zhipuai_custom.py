from itertools import count
from typing import Any, Dict, List, Optional

from langchain_core.embeddings import Embeddings
from langchain_core.pydantic_v1 import BaseModel, root_validator
from langchain_core.utils import get_from_dict_or_env
from packaging.version import parse
from importlib.metadata import version
import asyncio
import logging

logger = logging.getLogger(__name__)


def is_zhipu_v2() -> bool:
    """Return whether zhipu API is v2 or more."""
    _version = parse(version("zhipuai"))
    return _version.major >= 2


# Official Website: https://open.bigmodel.cn/dev/api#text_embedding
# An API-key is required to use this embedding model. You can get one by registering
class ZhipuaiTextEmbeddings(BaseModel, Embeddings):
    """Zhipuai Text Embedding models."""

    client: Any  # ZhipuAI  #: :meta private:
    model_name: str = "embedding-2"
    zhipuai_api_key: Optional[str] = None
    count_token: int = 0

    @root_validator(allow_reuse=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that auth token exists in environment."""

        try:
            from zhipuai import ZhipuAI

            if not is_zhipu_v2():
                raise RuntimeError(
                    "zhipuai package version is too low"
                    "Please install it via 'pip install --upgrade zhipuai'"
                )

            zhipuai_api_key = get_from_dict_or_env(
                values, "zhipuai_api_key", "ZHIPUAI_API_KEY"
            )

            client = ZhipuAI(
                api_key=zhipuai_api_key,
            )
            values["client"] = client
            return values
        except ImportError:
            raise RuntimeError(
                "Could not import zhipuai package. "
                "Please install it via 'pip install zhipuai'"
            )

    def _embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Internal method to call Zhipuai Embedding API and return embeddings.

        Args:
            texts: A list of texts to embed.

        Returns:
            A list of list of floats representing the embeddings, or None if an
            error occurs.
        """
        # try:
        #     return [self._get_embedding(text) for text in texts]

        # except Exception as e:
        #     logger.exception(e)
        #     # Log the exception or handle it as needed
        #     logger.info(
        #         f"Exception occurred while trying to get embeddings: {str(e)}"
        #     )  # noqa: T201
        #     return None
        return asyncio.run(self._aembed(texts))

    def embed_documents(self, texts: List[str]) -> Optional[List[List[float]]]:  # type: ignore[override]
        """Public method to get embeddings for a list of documents.

        Args:
            texts: The list of texts to embed.

        Returns:
            A list of embeddings, one for each text, or None if an error occurs.
        """
        return self._embed(texts)

    def embed_query(self, text: str) -> Optional[List[float]]:  # type: ignore[override]
        """Public method to get embedding for a single query text.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text, or None if an error occurs.
        """
        result = self._embed([text])
        return result[0] if result is not None else None

    def _get_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text)
        self.count_token += response.usage.total_tokens
        return response.data[0].embedding

    async def _aet_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text)
        self.count_token += response.usage.total_tokens  # 统计token
        return response.data[0].embedding

    async def _aembed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Internal method to call Zhipuai Embedding API and return embeddings.

        Args:
            texts: A list of texts to embed.

        Returns:
            A list of list of floats representing the embeddings, or None if an
            error occurs.
        """
        try:
            tasks = [asyncio.create_task(self._aet_embedding(text)) for text in texts]
            return await asyncio.gather(*tasks)

        except Exception as e:
            logger.exception(e)
            # Log the exception or handle it as needed
            logger.info(
                f"Exception occurred while trying to get embeddings: {str(e)}"
            )  # noqa: T201
            return None

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Asynchronous Embed search docs."""
        return await self._aembed(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """Asynchronous Embed query text."""
        result = await self._aembed([text])
        return result[0] if result is not None else None


if __name__ == "__main__":

    # async def main():
    #     client = ZhipuaiTextEmbeddings(
    #         zhipuai_api_key="69c26b8240f40e316f2b6a20c991fde2.3X8YMXlh8udmdhwJ"
    #     )

    #     print(
    #         await client.aembed_documents(
    #             ["你好，帝阅AI搜索", "帝阅DeepRead", "帝阅No.1"]
    #         )
    #     )

    # asyncio.run(main())

    client = ZhipuaiTextEmbeddings(
        zhipuai_api_key="69c26b8240f40e316f2b6a20c991fde2.3X8YMXlh8udmdhwJ"
    )
    client.embed_documents(["你好，帝阅AI搜索", "帝阅DeepRead", "帝阅No.1"])
    print(client.count_token)
