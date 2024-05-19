from langchain_community.document_loaders.async_html import AsyncHtmlLoader
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from typing import List, cast

import aiohttp
from langchain_core.documents import Document


logger = logging.getLogger(__name__)


class SearXNGAsyncHtmlLoader(AsyncHtmlLoader):

    async def _fetch(
        self,
        url: str,
        retries: int = 1,
        cooldown: int = 2,
        backoff: float = 1.5,
        timeout: int = 10,
    ) -> str:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            for i in range(retries):
                try:
                    async with session.get(
                        url,
                        headers=self.session.headers,
                        ssl=None if self.session.verify else False,
                    ) as response:
                        try:
                            text = await response.text()
                        except UnicodeDecodeError:
                            logger.error(f"Failed to decode content from {url}")
                            text = ""
                        return text
                except aiohttp.ClientConnectionError as e:
                    if i == retries - 1 and self.ignore_load_errors:
                        logger.warning(f"Error fetching {url} after {retries} retries.")
                        return ""
                    elif i == retries - 1:
                        raise
                    else:
                        logger.warning(
                            f"Error fetching {url} with attempt "
                            f"{i + 1}/{retries}: {e}. Retrying..."
                        )
                        await asyncio.sleep(cooldown * backoff**i)

    def load(self) -> List[Document]:
        """Load text from the url(s) in web_path."""

        try:
            # Raises RuntimeError if there is no current event loop.
            asyncio.get_running_loop()
            # If there is a current event loop, we need to run the async code
            # in a separate loop, in a separate thread.
            with ThreadPoolExecutor(
                max_workers=multiprocessing.cpu_count()
            ) as executor:
                future = executor.submit(asyncio.run, self.fetch_all(self.web_paths))
                results = future.result()
        except RuntimeError:
            results = asyncio.run(self.fetch_all(self.web_paths))
        docs = []
        for i, text in enumerate(cast(List[str], results)):
            docs.append(Document(page_content=text, metadata={"index": i}))

        return docs
