import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Union, Optional
from langchain_searxng.server.utils.auth import authenticated
from langchain_searxng.server.search.search_service import (
    SearchRequest,
    SearchService,
)
from langchain_searxng.server.search.search_handler import (
    zhipuai_event_generator,
    searxng_event_generator,
    searxng_event_generator_v2,
    searxng_invoke_v2,
    searxng_invoke,
    zhipuai_invoke,
    SearchResponse,
    check_search_mode,
)
from langchain_searxng.server.utils.model import (
    RestfulModel,
    SystemErrorCode,
)
from sse_starlette.sse import EventSourceResponse
from uuid import UUID

logger = logging.getLogger(__name__)

search_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])
search_router_v2 = APIRouter(prefix="/v2", dependencies=[Depends(authenticated)])


@search_router_v2.post(
    "/search/sse",
    tags=["Search"],
)
async def search_sse_v2(request: Request, body: SearchRequest):
    """
    Streaming search results over http sse
    """
    service = request.state.injector.get(SearchService)
    if check_search_mode(body, service):
        return EventSourceResponse(zhipuai_event_generator(request, body, service))
    else:
        return EventSourceResponse(searxng_event_generator_v2(request, body, service))


@search_router_v2.post(
    "/search/invoke",
    response_model=RestfulModel[SearchResponse | int | None],
    tags=["Search"],
)
async def search_invoke_v2(request: Request, body: SearchRequest) -> RestfulModel:
    """
    Call directly to return search results
    """
    service = request.state.injector.get(SearchService)
    if check_search_mode(body, service):
        return await zhipuai_invoke(request, body, service)
    else:
        return await searxng_invoke_v2(request, body, service)


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
    return await searxng_invoke(request, body, service)


@search_router.post(
    "/search/sse",
    tags=["Search"],
)
async def search_sse(request: Request, body: SearchRequest):
    """
    Streaming search results over http sse
    """
    service = request.state.injector.get(SearchService)
    return EventSourceResponse(searxng_event_generator(request, body, service))


@search_router.post(
    "/search/zhipuai/invoke",
    response_model=RestfulModel[SearchResponse | int | None],
    tags=["Search"],
)
async def search_zhipuai_invoke(request: Request, body: SearchRequest) -> RestfulModel:
    """
    Call directly to return search results
    """
    service = request.state.injector.get(SearchService)
    return await zhipuai_invoke(request, body, service)


@search_router.post(
    "/search/zhipuai/sse",
    tags=["Search"],
)
async def search_zhipuai_sse(request: Request, body: SearchRequest):
    """
    Streaming search results over http sse
    """
    service = request.state.injector.get(SearchService)

    return EventSourceResponse(zhipuai_event_generator(request, body, service))


class SendFeedbackBody(BaseModel):
    run_id: UUID
    key: str = "user_score"

    score: Union[float, int, bool, None] = None
    feedback_id: Optional[UUID] = None
    comment: Optional[str] = None


@search_router.post(
    "/feedback",
    tags=["Search"],
)
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


@search_router.post(
    "/get_trace",
    tags=["Search"],
)
async def get_trace(request: Request, body: GetTraceBody):
    service = request.state.injector.get(SearchService)

    run_id = body.run_id
    if run_id is None:
        return RestfulModel(
            code=SystemErrorCode, msg="No LangSmith run ID provided", data=None
        )
    return RestfulModel(data=await service.trace_service.aget_trace_url(str(run_id)))
