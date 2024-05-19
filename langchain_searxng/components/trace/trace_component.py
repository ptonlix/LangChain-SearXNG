import logging

from injector import inject, singleton
from langchain_searxng.settings.settings import Settings
from langsmith import Client
from langsmith.utils import LangSmithError
import os
import asyncio

logger = logging.getLogger(__name__)


@singleton
class TraceComponent:
    @inject
    def __init__(self, settings: Settings) -> None:
        os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langsmith.trace_version_v2)
        os.environ["LANGCHAIN_PROJECT"] = str(settings.langsmith.langchain_project)
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith.api_key
        self.trace_client = Client(api_key=settings.langsmith.api_key)

    async def _arun(self, func, *args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(
            None, func, *args, **kwargs
        )

    async def aget_trace_url(self, run_id: str) -> str:
        for i in range(5):
            try:
                await self._arun(self.trace_client.read_run, run_id)
                break
            except LangSmithError:
                await asyncio.sleep(1**i)

        if await self._arun(self.trace_client.run_is_shared, run_id):
            return await self._arun(self.trace_client.read_run_shared_link, run_id)
        return await self._arun(self.trace_client.share_run, run_id)
