import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Any

from langchain_searxng.server.utils.auth import authenticated
from langchain_searxng.server.search.search_service import (
    SearchRequest,
    SearchService,
    ReadRunIdAsyncHandler,
    CalTokenNumAsyncHandler,
    TokenInfo,
)
from langchain_searxng.server.utils.model import (
    RestfulModel,
    SystemErrorCode,
    ChatHistoryTooLong,
)
from langchain_community.callbacks import get_openai_callback
from langchain_searxng.components.llm.custom.zhipuai import get_zhipuai_callback
from langchain_searxng.components.searxng.searxng_component import DocSource
from uuid import UUID

logger = logging.getLogger(__name__)

search_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])


class SearchResponse(BaseModel):
    run_id: UUID
    answer: str
    source: List[Any]
    searchresult: List[Any]
    token_info: TokenInfo


"""
一共有六种消息类型 event
- message : 正常流式消息
- error : 错误消息
- source : 引用文章来源信息，包括文章链接等
- tokeninfo: 全部消耗的Token信息
- runid : 链ID,方便调试追踪
- complete: 完整的答复消息，方便记录
"""


class SearchSseResponse(BaseModel):
    event: str
    data: Any
    retry: int = Field(default=15000)


async def searxng_event_generator(
    request: Request, body: SearchRequest, service: SearchService
):
    try:
        final_output = None
        calltoken = CalTokenNumAsyncHandler(
            llm_model=body.llm,
            token_model=service.llm_service.modelname,
        )

        chat_len, flag = service.check_chat_len(body)
        if not flag:
            logger.info(f"The message you submitted was too long : {chat_len}")
            yield SearchSseResponse(
                event="error",
                data=RestfulModel(
                    code=ChatHistoryTooLong,
                    msg=str(
                        "The message you submitted was too long, please reload the conversation and submit something shorter."
                    ),
                    data=chat_len,
                ),
            ).model_dump()
            return

        async for chunk in service.chain.astream_log(
            input={
                "question": body.question,
                "chat_history": body.chat_history,
                "network": body.network,
            },
            config={
                "metadata": {
                    "conversation_id": body.conversation_id,
                },
                "configurable": {"retriever": body.retriever, "llm": body.llm},
                "callbacks": [calltoken],
            },
            include_names=["FinalSourceRetriever", "Retriever"],
        ):
            if await request.is_disconnected():
                logger.warning("The connection has been interrupted.")
                break
            for op in chunk.ops:
                # 流式返回来源信息
                if "Retriever/final_output" in op["path"]:
                    for doc in op["value"]["documents"]:
                        yield SearchSseResponse(
                            event="source",
                            data=DocSource(
                                title=doc.metadata.get("title"),
                                source_link=doc.metadata.get("source"),
                                description=doc.metadata.get("description"),
                            ),
                        ).model_dump()

                if len(op["path"]) == 0:
                    yield SearchSseResponse(
                        event="runid", data=op["value"]["id"]
                    ).model_dump()
                elif "FinalSourceRetriever/final_output" in op["path"]:
                    logger.info(op["value"])
                elif "streamed_output" in op["path"]:
                    yield SearchSseResponse(
                        event="message", data=op["value"]
                    ).model_dump()
                elif "final_output" in op["path"]:
                    final_output = op["value"]

        yield SearchSseResponse(event="complete", data=final_output).model_dump()

        yield SearchSseResponse(
            event="source_complete",
            data=[
                docs.copy()
                for docs in service.searxng_service.search_retriever.get_docsource_list()
            ],
        ).model_dump()
        # service.searxng_service.search_retriever.clear_docsource_list()

        embed_tokens = service.embedding_service.total_tokens
        logger.info(f"embedding token: {embed_tokens}")

        yield SearchSseResponse(
            event="token_info", data=calltoken.get_token_info(embed_tokens)
        ).model_dump()

    except Exception as e:
        logger.exception(e)
        yield SearchSseResponse(event="error", data=str(e)).model_dump()


async def searxng_invoke(
    request: Request, body: SearchRequest, service: SearchService
) -> RestfulModel:
    chat_len, flag = service.check_chat_len(body)
    if not flag:
        logger.info(f"The message you submitted was too long : {chat_len}")
        return RestfulModel(
            code=ChatHistoryTooLong,
            msg=str(
                "The message you submitted was too long, please reload the conversation and submit something shorter."
            ),
            data=chat_len,
        )
    try:
        with get_openai_callback() as cb:

            read_runid = ReadRunIdAsyncHandler()  # 读取runid回调
            result = await service.chain.ainvoke(
                input={
                    "question": body.question,
                    "chat_history": body.chat_history,
                    "network": body.network,
                },
                config={
                    "metadata": {
                        "conversation_id": body.conversation_id,
                    },
                    "configurable": {"retriever": body.retriever, "llm": body.llm},
                    "callbacks": [cb, read_runid],
                },
            )

            embed_tokens = service.embedding_service.total_tokens
            logger.info(f"embedding token: {embed_tokens}")

            tokeninfo = TokenInfo(
                model=body.llm,
                total_tokens=cb.total_tokens + int(embed_tokens / 10),
                prompt_tokens=cb.prompt_tokens,
                completion_tokens=cb.completion_tokens,
                successful_requests=cb.successful_requests,
                embedding_tokens=int(embed_tokens / 10),
                total_cost=cb.total_cost,
            )

            resobj = SearchResponse(
                run_id=read_runid.get_runid(),
                token_info=tokeninfo,
                answer=result,
                source=[
                    docs.copy()
                    for docs in service.searxng_service.search_retriever.get_docsource_list()
                ],
                searchresult=[],
            )
            # service.searxng_service.search_retriever.clear_docsource_list()
            return RestfulModel(data=resobj)
    except Exception as e:
        logger.exception(e)
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)


async def zhipuai_event_generator(
    request: Request, body: SearchRequest, service: SearchService
):
    try:
        final_output = None
        chat_len, flag = service.check_chat_len(body)
        if not flag:
            logger.info(f"The message you submitted was too long : {chat_len}")
            yield SearchSseResponse(
                event="error",
                data=RestfulModel(
                    code=ChatHistoryTooLong,
                    msg=str(
                        "The message you submitted was too long, please reload the conversation and submit something shorter."
                    ),
                    data=chat_len,
                ),
            ).model_dump()
            return

        with get_zhipuai_callback() as cb:
            async for chunk in service.zhipu_chain.astream_log(
                input={
                    "question": body.question,
                    "chat_history": body.chat_history,
                    "network": body.network,
                },
                config={
                    "metadata": {
                        "conversation_id": body.conversation_id,
                    },
                    "configurable": {"llm": body.llm},
                    "callbacks": [cb],
                },
                include_names=["FinalSourceRetriever", "Retriever"],
            ):
                if await request.is_disconnected():
                    logger.warning("The connection has been interrupted.")
                    break
                for op in chunk.ops:
                    if len(op["path"]) == 0:
                        yield SearchSseResponse(
                            event="runid", data=op["value"]["id"]
                        ).model_dump()
                    elif "streamed_output" in op["path"]:
                        yield SearchSseResponse(
                            event="message", data=op["value"]
                        ).model_dump()
                    elif "final_output" in op["path"]:
                        final_output = op["value"]

            yield SearchSseResponse(event="complete", data=final_output).model_dump()

            yield SearchSseResponse(
                event="source_complete",
                data=service.convert_zhipu_to_docsource(cb.web_search),
            ).model_dump()

            tokeninfo = TokenInfo(
                model="zhipuai",
                total_tokens=cb.total_tokens,
                prompt_tokens=cb.prompt_tokens,
                completion_tokens=cb.completion_tokens,
                successful_requests=cb.successful_requests,
                total_cost=cb.total_cost,
            )

            yield SearchSseResponse(event="token_info", data=tokeninfo).model_dump()

    except Exception as e:
        logger.exception(e)
        yield SearchSseResponse(event="error", data=str(e)).model_dump()


async def zhipuai_invoke(
    request: Request, body: SearchRequest, service: SearchService
) -> RestfulModel:
    chat_len, flag = service.check_chat_len(body)
    if not flag:
        logger.info(f"The message you submitted was too long : {chat_len}")
        return RestfulModel(
            code=ChatHistoryTooLong,
            msg=str(
                "The message you submitted was too long, please reload the conversation and submit something shorter."
            ),
            data=chat_len,
        )

    try:
        with get_zhipuai_callback() as cb:
            read_runid = ReadRunIdAsyncHandler()  # 读取runid回调
            result = await service.zhipu_chain.ainvoke(
                input={
                    "question": body.question,
                    "chat_history": body.chat_history,
                    "network": body.network,
                },
                config={
                    "metadata": {
                        "conversation_id": body.conversation_id,
                    },
                    "configurable": {"llm": body.llm},
                    "callbacks": [cb, read_runid],
                },
            )

            tokeninfo = TokenInfo(
                model="zhipuai",
                total_tokens=cb.total_tokens,
                prompt_tokens=cb.prompt_tokens,
                completion_tokens=cb.completion_tokens,
                successful_requests=cb.successful_requests,
                total_cost=cb.total_cost,
            )

            resobj = SearchResponse(
                run_id=read_runid.get_runid(),
                token_info=tokeninfo,
                answer=result,
                source=service.convert_zhipu_to_docsource(cb.web_search),
                searchresult=[],
            )
            return RestfulModel(data=resobj)
    except Exception as e:
        logger.exception(e)
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)


def check_search_mode(body: SearchRequest, service: SearchService) -> bool:
    if body.llm == "zhipuwebsearch" and body.retriever == "zhipuwebsearch":
        if service.settings.llm.mode in ["zhipuwebsearch", "all"]:
            return True
    return False


async def searxng_invoke_v2(
    request: Request, body: SearchRequest, service: SearchService
) -> RestfulModel:
    chat_len, flag = service.check_chat_len(body)
    if not flag:
        logger.info(f"The message you submitted was too long : {chat_len}")
        return RestfulModel(
            code=ChatHistoryTooLong,
            msg=str(
                "The message you submitted was too long, please reload the conversation and submit something shorter."
            ),
            data=chat_len,
        )
    try:
        with get_openai_callback() as cb:

            searxng_v2_cb = ReadRunIdAsyncHandler()  # 读取runid回调
            result = await service.chain_v2.ainvoke(
                input={
                    "question": body.question,
                    "chat_history": body.chat_history,
                    "network": body.network,
                },
                config={
                    "metadata": {
                        "conversation_id": body.conversation_id,
                    },
                    "configurable": {"retriever": body.retriever, "llm": body.llm},
                    "callbacks": [cb, searxng_v2_cb],
                },
            )

            embed_tokens = service.embedding_service.total_tokens
            logger.info(f"embedding token: {embed_tokens}")

            tokeninfo = TokenInfo(
                model=body.llm,
                total_tokens=cb.total_tokens + int(embed_tokens / 10),
                prompt_tokens=cb.prompt_tokens,
                completion_tokens=cb.completion_tokens,
                successful_requests=cb.successful_requests,
                embedding_tokens=int(embed_tokens / 10),
                total_cost=cb.total_cost,
            )

            resobj = SearchResponse(
                run_id=searxng_v2_cb.get_runid(),
                token_info=tokeninfo,
                answer=result,
                source=searxng_v2_cb.get_source_doc(),
                searchresult=searxng_v2_cb.get_search_result(),
            )
            # service.searxng_service.search_retriever.clear_docsource_list()
            return RestfulModel(data=resobj)
    except Exception as e:
        logger.exception(e)
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)


async def searxng_event_generator_v2(
    request: Request, body: SearchRequest, service: SearchService
):
    try:
        final_output = None
        source_doc_list = []
        calltoken = CalTokenNumAsyncHandler(
            llm_model=body.llm,
            token_model=service.llm_service.modelname,
        )

        chat_len, flag = service.check_chat_len(body)
        if not flag:
            logger.info(f"The message you submitted was too long : {chat_len}")
            yield SearchSseResponse(
                event="error",
                data=RestfulModel(
                    code=ChatHistoryTooLong,
                    msg=str(
                        "The message you submitted was too long, please reload the conversation and submit something shorter."
                    ),
                    data=chat_len,
                ),
            ).model_dump()
            return

        async for chunk in service.chain_v2.astream_log(
            input={
                "question": body.question,
                "chat_history": body.chat_history,
                "network": body.network,
            },
            config={
                "metadata": {
                    "conversation_id": body.conversation_id,
                },
                "configurable": {"retriever": body.retriever, "llm": body.llm},
                "callbacks": [calltoken],
            },
            include_names=["FinalSourceRetriever", "Retriever", "SearXNGSearchResult"],
        ):
            if await request.is_disconnected():
                logger.warning("The connection has been interrupted.")
                break
            for op in chunk.ops:
                # 流式返回来源信息
                if "SearXNGSearchResult/final_output" in op["path"]:
                    yield SearchSseResponse(
                        event="searchresult", data=op["value"]["output"]
                    ).model_dump()

                if "FinalSourceRetriever/final_output" in op["path"]:
                    for doc in op["value"]["output"]:
                        source_doc_list.append(doc.metadata)
                        yield SearchSseResponse(
                            event="source", data=doc.metadata
                        ).model_dump()

                if len(op["path"]) == 0:
                    yield SearchSseResponse(
                        event="runid", data=op["value"]["id"]
                    ).model_dump()
                elif "/streamed_output/-" == op["path"]:
                    yield SearchSseResponse(
                        event="message", data=op["value"]
                    ).model_dump()
                elif "final_output" in op["path"]:
                    final_output = op["value"]

        yield SearchSseResponse(event="complete", data=final_output).model_dump()

        yield SearchSseResponse(
            event="source_complete",
            data=source_doc_list,
        ).model_dump()
        # service.searxng_service.search_retriever.clear_docsource_list()

        embed_tokens = service.embedding_service.total_tokens
        logger.info(f"embedding token: {embed_tokens}")

        yield SearchSseResponse(
            event="token_info", data=calltoken.get_token_info(embed_tokens)
        ).model_dump()

    except Exception as e:
        logger.exception(e)
        yield SearchSseResponse(event="error", data=str(e)).model_dump()
