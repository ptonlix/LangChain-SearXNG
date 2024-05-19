from injector import inject
from langchain_searxng.components.llm.llm_component import LLMComponent
from langchain_searxng.components.embedding.embedding_component import (
    EmbeddingComponent,
)
from langchain_searxng.components.searxng.searxng_component import (
    SearXNGComponent,
    DocSource,
)
from langchain_searxng.components.trace.trace_component import TraceComponent
from langchain_searxng.server.search.search_prompt import (
    RESPONSE_TEMPLATE,
    NO_NETWORK_RESPONSE_TEMPLATE,
    REPHRASE_TEMPLATE,
)
from langchain.schema.output_parser import StrOutputParser
from pydantic import BaseModel, Field
import logging
import tiktoken
from langchain_searxng.settings.settings import Settings
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema.messages import AIMessage, HumanMessage, BaseMessage
from langchain.schema.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.document_compressors import (
    DocumentCompressorPipeline,
    EmbeddingsFilter,
    LLMChainExtractor,
)
from langchain.retrievers import (
    ContextualCompressionRetriever,
)
from langchain.schema.runnable import (
    ConfigurableField,
    Runnable,
    RunnableBranch,
    RunnableLambda,
    RunnableMap,
)
from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.retriever import BaseRetriever
from langchain_core.embeddings import Embeddings
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.outputs import LLMResult
from uuid import UUID
from operator import itemgetter
from datetime import datetime

from typing import (
    List,
    Optional,
    Sequence,
    Tuple,
    Dict,
    Any,
)


logger = logging.getLogger(__name__)


class TokenInfo(BaseModel):
    model: str
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    embedding_tokens: int = 0
    successful_requests: int = 0
    total_cost: float = 0.0

    def clear(self):
        self.total_tokens = 0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.successful_requests: int = 0
        self.total_cost: float = 0.0


class SearchRequest(BaseModel):
    question: str
    network: bool
    chat_history: List[Tuple[str, str]] = Field(
        ...,
        extra={"widget": {"type": "chat", "input": "question", "output": "answer"}},
    )
    conversation_id: str
    retriever: str = Field(
        default="searx", description="搜索引擎"
    )  # searx, zhipuwebsearch
    llm: str = Field(default="openai", description="大模型")


"""
读取chain run_id的回调和引用文章信息
"""


class ReadRunIdAsyncHandler(AsyncCallbackHandler):

    def __init__(self):
        self.runid: UUID = None
        self.search_list = []
        self.source_doc_list = []

    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain starts running."""
        if not self.runid:
            self.runid = run_id

    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain ends running."""
        if (
            "branch:default" in tags
            and isinstance(outputs, List)
            and all(isinstance(item, Document) for item in outputs)
        ):
            for doc in outputs:
                self.source_doc_list.append(doc.metadata)

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any: ...

    async def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when tool ends running."""
        # logger.info(output)
        self.search_list = output

    def get_runid(self) -> UUID:
        return self.runid

    def get_source_doc(self) -> List[Dict]:
        return self.source_doc_list

    def get_search_result(self) -> List[Dict]:
        return self.search_list


class CalTokenNumAsyncHandler(AsyncCallbackHandler):
    """Async callback handler that can be used to handle callbacks from langchain."""

    def __init__(self, llm_model: str, token_model: str):
        self.llm_model = llm_model
        self.token_model = token_model
        self.token_info: TokenInfo = TokenInfo(model="openai")

    def num_tokens_from_string(self, string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(self.token_model)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when chain starts running."""
        for prompt in prompts:
            self.token_info.prompt_tokens += self.num_tokens_from_string(prompt)

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when chain ends running."""
        self.token_info.completion_tokens += self.num_tokens_from_string(
            response.generations[0][0].text
        )
        self.token_info.successful_requests += 1
        self.token_info.total_tokens = (
            self.token_info.prompt_tokens + self.token_info.completion_tokens
        )
        self.token_info.model = self.llm_model

    def get_token_info(self, embed_tokens: int) -> TokenInfo:
        self.token_info.total_tokens += int(embed_tokens / 10)
        return self.token_info


class SearchService:

    @inject
    def __init__(
        self,
        llm_component: LLMComponent,
        embedding_component: EmbeddingComponent,
        searxng_component: SearXNGComponent,
        trace_component: TraceComponent,
        settings: Settings,
    ) -> None:
        self.settings = settings
        self.llm_service = llm_component
        self.embedding_service = embedding_component
        self.searxng_service = searxng_component
        self.trace_service = trace_component
        self.chain = self.create_chain(
            self.llm_service.llm,
            self.get_searx_retriever_by_llm(self.llm_service.llm),
        )
        self.chain_v2 = self.create_chain(
            self.llm_service.llm,
            self.searxng_service.search_retriever_v2(self.llm_service.llm),
        )
        self.zhipu_chain = self.create_zhipu_chain(self.llm_service.llm)

    def num_tokens_from_string(self, string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(self.llm_service.modelname)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def get_searx_retriever_by_llm(self, llm: BaseLanguageModel):
        compressor = LLMChainExtractor.from_llm(llm)

        base_searx_retriever = self.searxng_service.search_retriever
        searx_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=base_searx_retriever
        )
        return searx_retriever.configurable_alternatives(
            # This gives this field an id
            # When configuring the end runnable, we can then use this id to configure this field
            ConfigurableField(id="retriever"),
            default_key="searx",
        ).with_config(run_name="FinalSourceRetriever")

    def get_searx_retriever_by_embed(self, embeddings: Embeddings):
        splitter = RecursiveCharacterTextSplitter(chunk_size=4096, chunk_overlap=0)
        relevance_filter = EmbeddingsFilter(
            embeddings=embeddings, similarity_threshold=0.8
        )
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[splitter, relevance_filter]
        )
        base_searx_retriever = self.searxng_service.search_retriever
        searx_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor, base_retriever=base_searx_retriever
        )

        return searx_retriever.configurable_alternatives(
            # This gives this field an id
            # When configuring the end runnable, we can then use this id to configure this field
            ConfigurableField(id="retriever"),
            default_key="searx",
        ).with_config(run_name="FinalSourceRetriever")

    def create_retriever_chain(
        self, llm: BaseLanguageModel, retriever: BaseRetriever
    ) -> Runnable:
        CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(REPHRASE_TEMPLATE)
        condense_question_chain = (
            CONDENSE_QUESTION_PROMPT | llm | StrOutputParser()
        ).with_config(
            run_name="CondenseQuestion",
        )
        conversation_chain = condense_question_chain | retriever
        return RunnableBranch(
            (
                RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
                    run_name="HasChatHistoryCheck"
                ),
                conversation_chain.with_config(run_name="RetrievalChainWithHistory"),
            ),
            (
                RunnableLambda(itemgetter("question")).with_config(
                    run_name="Itemgetter:question"
                )
                | retriever
            ).with_config(run_name="RetrievalChainWithNoHistory"),
        ).with_config(run_name="RouteDependingOnChatHistory")

    def serialize_history(self, request: SearchRequest):
        chat_history = request.get("chat_history", [])
        converted_chat_history = []
        for message in chat_history:
            if message[0] == "human":
                converted_chat_history.append(HumanMessage(content=message[1]))
            elif message[0] == "ai":
                converted_chat_history.append(AIMessage(content=message[1]))
        return converted_chat_history

    def format_docs(self, docs: Sequence[Document]) -> str:
        formatted_docs = []
        formatted_docs_str = ""
        for i, doc in enumerate(docs):
            content = doc.page_content
            doc_string = f"<doc id='{i}'>{content}</doc>"
            formatted_docs.append(doc_string)
            formatted_docs_str = "\n".join(formatted_docs)
            if (
                len(formatted_docs_str) >= 20000
            ):  # 一次请求不能超过20000字节，减少Token消耗
                logger.info("answer formatted_docs is too long.")
                break
        logger.info(f"answer formatted_docs length: {len(formatted_docs_str)} done")
        return formatted_docs_str

    """
    判断聊天长度是否超过模型输入的窗口大小
    """

    def check_chat_len(self, request: SearchRequest) -> Tuple[int, bool]:
        chat_str = ""
        for message in request.chat_history:
            for m in message:
                chat_str += m
        chat_str += request.question

        chat_history_tokens = self.num_tokens_from_string(chat_str)

        # logger.info(f"check chathistory len : {chat_str}")

        if request.llm == "openai" and chat_history_tokens > 12000:  # 上下文16K
            return chat_history_tokens, False
        elif request.llm == "zhipuai" and chat_history_tokens > 123000:  # 上下文128K
            return chat_history_tokens, False

        return chat_history_tokens, True

    def create_chain(
        self,
        llm: BaseLanguageModel,
        retriever: BaseRetriever,
    ) -> Runnable:
        retriever_chain = self.create_retriever_chain(llm, retriever) | RunnableLambda(
            self.format_docs
        ).with_config(run_name="FormatDocumentChunks")
        _context = RunnableMap(
            {
                "context": retriever_chain.with_config(run_name="RetrievalChain"),
                "question": RunnableLambda(itemgetter("question")).with_config(
                    run_name="Itemgetter:question"
                ),
                "chat_history": RunnableLambda(itemgetter("chat_history")).with_config(
                    run_name="Itemgetter:chat_history"
                ),
            }
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RESPONSE_TEMPLATE),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        ).partial(current_date=datetime.now().isoformat())

        response_synthesizer = (prompt | llm | StrOutputParser()).with_config(
            run_name="GenerateResponse",
        )

        no_network_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", NO_NETWORK_RESPONSE_TEMPLATE),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        ).partial(current_date=datetime.now().isoformat())

        no_network_response_synthesizer = (
            no_network_prompt | llm | StrOutputParser()
        ).with_config(
            run_name="GenerateResponse",
        )
        return {
            "question": RunnableLambda(itemgetter("question")).with_config(
                run_name="Itemgetter:question"
            ),
            "chat_history": RunnableLambda(self.serialize_history).with_config(
                run_name="SerializeHistory"
            ),
            "network": RunnableLambda(itemgetter("network")).with_config(
                run_name="Itemgetter:network"
            ),
        } | RunnableBranch(
            (
                RunnableLambda(lambda x: bool(x.get("network"))).with_config(
                    run_name="HasNetworkCheck"
                ),
                (_context | response_synthesizer).with_config(
                    run_name="ContextChainWithNetwork"
                ),
            ),
            (
                RunnableMap(
                    {
                        "question": RunnableLambda(itemgetter("question")).with_config(
                            run_name="Itemgetter:question"
                        ),
                        "chat_history": RunnableLambda(
                            itemgetter("chat_history")
                        ).with_config(run_name="Itemgetter:chat_history"),
                    }
                )
                | no_network_response_synthesizer
            ).with_config(run_name="ContextChainWithNoNetwork"),
        ).with_config(
            run_name="RouteDependingOnNetwork"
        )

    def convert_zhipu_to_docsource(
        self, websearch: List[Dict[str, str]]
    ) -> List[DocSource]:
        try:
            for obj in websearch:
                if "link" in obj:
                    obj["url"] = obj.pop("link")
            return websearch
        except Exception:
            return []

    def create_zhipu_chain(self, llm: BaseLanguageModel):

        _prompt = ChatPromptTemplate.from_messages(
            [
                ("system", NO_NETWORK_RESPONSE_TEMPLATE),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        ).partial(current_date=datetime.now().isoformat())

        no_network_response_synthesizer = (
            _prompt
            | llm.bind(
                tools=[
                    {
                        "type": "web_search",
                        "web_search": {"enable": False},
                    }
                ],
            )
            | StrOutputParser()
        ).with_config(
            run_name="GenerateResponse",
        )

        network_response_synthesizer = (
            _prompt
            | llm.bind(
                tools=[
                    {
                        "type": "web_search",
                        "web_search": {
                            "enable": True,
                            "search_result": True,
                        },
                    }
                ],
            )
            | StrOutputParser()
        ).with_config(
            run_name="GenerateResponse",
        )

        return {
            "question": RunnableLambda(itemgetter("question")).with_config(
                run_name="Itemgetter:question"
            ),
            "chat_history": RunnableLambda(self.serialize_history).with_config(
                run_name="SerializeHistory"
            ),
            "network": RunnableLambda(itemgetter("network")).with_config(
                run_name="Itemgetter:network"
            ),
        } | RunnableBranch(
            (
                RunnableLambda(lambda x: bool(x.get("network"))).with_config(
                    run_name="HasNetworkCheck"
                ),
                network_response_synthesizer.with_config(
                    run_name="ContextChainWithNetwork"
                ),
            ),
            no_network_response_synthesizer.with_config(
                run_name="ContextChainWithNoNetwork"
            ),
        ).with_config(
            run_name="RouteDependingOnNetwork"
        )
