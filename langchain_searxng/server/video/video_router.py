import logging
from fastapi import APIRouter, Depends, Request
from langchain_searxng.server.utils.auth import authenticated
from langchain_searxng.server.video.video_service import (
    VideoSearchRequest,
    VideoSearchResponse,
    VideoService,
)
from langchain_searxng.server.utils.model import (
    RestfulModel,
    SystemErrorCode,
)


logger = logging.getLogger(__name__)

video_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])


@video_router.post(
    "/search/video",
    response_model=RestfulModel[VideoSearchResponse | int | None],
    tags=["SearchVideo"],
)
async def search_video(request: Request, body: VideoSearchRequest) -> RestfulModel:
    """
    Call directly to return search results
    """
    service = request.state.injector.get(VideoService)
    try:
        return RestfulModel(data=await service.search_bilibli_video(body))
    except Exception as e:
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)
