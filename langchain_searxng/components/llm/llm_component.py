import logging

from injector import inject, singleton

# from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.llms.base import BaseLanguageModel
from langchain.llms.fake import FakeListLLM
from langchain_searxng.settings.settings import Settings
from langchain_searxng.components.llm.custom.zhipuai import ChatZhipuAI
from langchain.schema.runnable import ConfigurableField

logger = logging.getLogger(__name__)


@singleton
class LLMComponent:
    @inject
    def __init__(self, settings: Settings) -> None:
        llm_mode = settings.llm.mode
        logger.info("Initializing the LLM in mode=%s", llm_mode)
        self.modelname = settings.openai.modelname
        match settings.llm.mode:
            case "local":
                ...  # Todo
            case "openai":
                openai_settings = settings.openai
                self._llm = ChatOpenAI(
                    temperature=openai_settings.temperature,
                    model_name=openai_settings.modelname,
                    api_key=openai_settings.api_key,
                    openai_api_base=openai_settings.api_base,
                ).configurable_alternatives(
                    # This gives this field an id
                    # When configuring the end runnable, we can then use this id to configure this field
                    ConfigurableField(id="llm"),
                    default_key="openai",
                )

            case "zhipuai":
                zhipuai_settings = settings.zhipuai
                self._llm = ChatOpenAI(
                    model=zhipuai_settings.modelname,
                    temperature=zhipuai_settings.temperature,
                    openai_api_base=zhipuai_settings.api_base,
                    api_key=zhipuai_settings.api_key,
                ).configurable_alternatives(
                    # This gives this field an id
                    # When configuring the end runnable, we can then use this id to configure this field
                    ConfigurableField(id="llm"),
                    default_key="zhipuai",
                )
            case "deepseek":
                deepseek_settings = settings.deepseek
                self._llm = ChatOpenAI(
                    model=deepseek_settings.modelname,
                    temperature=deepseek_settings.temperature,
                    openai_api_base=deepseek_settings.api_base,
                    api_key=deepseek_settings.api_key,
                ).configurable_alternatives(
                    # This gives this field an id
                    # When configuring the end runnable, we can then use this id to configure this field
                    ConfigurableField(id="llm"),
                    default_key="deepseek",
                )

            case "zhipuwebsearch":
                zhipuai_settings = settings.zhipuai
                self._llm = ChatZhipuAI(
                    model=zhipuai_settings.modelname,
                    temperature=zhipuai_settings.temperature,
                    top_p=zhipuai_settings.top_p,
                    api_key=zhipuai_settings.api_key,
                ).configurable_alternatives(
                    # This gives this field an id
                    # When configuring the end runnable, we can then use this id to configure this field
                    ConfigurableField(id="llm"),
                    default_key="zhipuwebsearch",
                )

            case "all":
                openai_settings = settings.openai
                zhipuai_settings = settings.zhipuai
                deepseek_settings = settings.deepseek
                self._llm = ChatOpenAI(
                    temperature=openai_settings.temperature,
                    model_name=openai_settings.modelname,
                    api_key=openai_settings.api_key,
                    openai_api_base=openai_settings.api_base,
                ).configurable_alternatives(
                    # This gives this field an id
                    # When configuring the end runnable, we can then use this id to configure this field
                    ConfigurableField(id="llm"),
                    default_key="openai",
                    zhipuai=ChatOpenAI(
                        model=zhipuai_settings.modelname,
                        temperature=zhipuai_settings.temperature,
                        openai_api_base=zhipuai_settings.api_base,
                        api_key=zhipuai_settings.api_key,
                    ),
                    deepseek=ChatOpenAI(
                        model=deepseek_settings.modelname,
                        temperature=deepseek_settings.temperature,
                        openai_api_base=deepseek_settings.api_base,
                        api_key=deepseek_settings.api_key,
                    ),
                    zhipuwebsearch=ChatZhipuAI(
                        model=zhipuai_settings.modelname,
                        temperature=zhipuai_settings.temperature,
                        top_p=zhipuai_settings.top_p,
                        api_key=zhipuai_settings.api_key,
                    ),
                )

            case "mock":
                self._llm = FakeListLLM(
                    responses=["你好,帝阅AI搜索"]
                ).configurable_alternatives(
                    # This gives this field an id
                    # When configuring the end runnable, we can then use this id to configure this field
                    ConfigurableField(id="llm"),
                    default_key="mock",
                )

    @property
    def llm(self) -> BaseLanguageModel:
        return self._llm
