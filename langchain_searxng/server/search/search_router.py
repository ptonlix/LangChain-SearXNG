import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Any, Union, Optional
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
from sse_starlette.sse import EventSourceResponse
from uuid import UUID

logger = logging.getLogger(__name__)

search_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])


class SearchResponse(BaseModel):
    run_id: UUID
    answer: str
    soucre: List[Any]
    tokeninfo: TokenInfo


@search_router.post(
    "/search/invoke",
    response_model=RestfulModel[SearchResponse | int | None],
    tags=["Search"],
)
async def search_invoke(request: Request, body: SearchRequest) -> RestfulModel:
    """
    Call directly to return search results
    """
    service = request.state.injector.get(SearchService)
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

    token_callback = (
        get_openai_callback if body.llm == "openai" else get_zhipuai_callback
    )
    try:
        with token_callback() as cb:
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
                tokeninfo=tokeninfo,
                answer=result,
                soucre=[
                    docs.copy()
                    for docs in service.searxng_service.search_retriever.get_docsource_list()
                ],
            )
            # service.searxng_service.search_retriever.clear_docsource_list()
            return RestfulModel(data=resobj)
    except Exception as e:
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)


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


@search_router.post("/search/sse")
async def search_sse(request: Request, body: SearchRequest):
    """
    Streaming search results over http sse
    """
    service = request.state.injector.get(SearchService)

    async def event_generator(request: Request):
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
                include_names=["FinalSourceRetriever"],
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
                event="source",
                data=[
                    docs.copy()
                    for docs in service.searxng_service.search_retriever.get_docsource_list()
                ],
            ).model_dump()
            # service.searxng_service.search_retriever.clear_docsource_list()

            embed_tokens = service.embedding_service.total_tokens
            logger.info(f"embedding token: {embed_tokens}")

            yield SearchSseResponse(
                event="tokeninfo", data=calltoken.get_token_info(embed_tokens)
            ).model_dump()

        except Exception as e:
            logger.exception(e)
            yield SearchSseResponse(event="error", data=str(e)).model_dump()

    return EventSourceResponse(event_generator(request))


class SendFeedbackBody(BaseModel):
    run_id: UUID
    key: str = "user_score"

    score: Union[float, int, bool, None] = None
    feedback_id: Optional[UUID] = None
    comment: Optional[str] = None


@search_router.post("/feedback")
async def send_feedback(request: Request, body: SendFeedbackBody):
    service = request.state.injector.get(SearchService)
    service.trace_service.trace_client.create_feedback(
        body.run_id,
        body.key,
        score=body.score,
        comment=body.comment,
        feedback_id=body.feedback_id,
    )
    return RestfulModel(data="posted feedback successfully")


class GetTraceBody(BaseModel):
    run_id: UUID


@search_router.post("/get_trace")
async def get_trace(request: Request, body: GetTraceBody):
    service = request.state.injector.get(SearchService)

    run_id = body.run_id
    if run_id is None:
        return RestfulModel(
            code=SystemErrorCode, msg="No LangSmith run ID provided", data=None
        )
    return RestfulModel(data=await service.trace_service.aget_trace_url(str(run_id)))
