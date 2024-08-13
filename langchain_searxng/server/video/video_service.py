from injector import inject
from langchain_searxng.settings.settings import Settings
from pydantic import BaseModel, Field
from bilibili_api import search
from enum import Enum
from typing import List
import logging

logger = logging.getLogger(__name__)


class VideoSearchRequest(BaseModel):
    query: str
    page: int = Field(default=1, description="搜索页码")
    pagesize: int = Field(default=5, description="搜索个数")
    conversation_id: str = Field(description="搜索对话ID")


class VideoSearchResult(BaseModel):
    arcurl: str = Field(description="视频链接")
    author: str = Field(description="视频作者")
    pic: str = Field(description="视频导图")
    description: str = Field(description="描述")
    pubdate: int = Field(description="视频发布时间")
    duration: str = Field(description="视频时长")


class VideoPlatform(Enum):
    BiliBili = 0
    Youtube = 1


class VideoSearchResponse(BaseModel):
    video_platform: VideoPlatform = Field(description="视频平台")
    video_list: List[VideoSearchResult]


class VideoService:
    @inject
    def __init__(
        self,
        settings: Settings,
    ) -> None:
        self.settings = settings

    async def search_bilibli_video(
        self, req: VideoSearchRequest
    ) -> VideoSearchResponse:
        try:
            data = await search.search_by_type(
                req.query,
                search_type=search.SearchObjectType.VIDEO,
                order_type=search.OrderVideo.TOTALRANK,
                page=req.page,
                page_size=req.pagesize,
                order_sort=0,
            )
            video_list = [
                VideoSearchResult(
                    arcurl=obj["arcurl"],
                    author=obj["author"],
                    pic="http://" + obj["pic"],
                    description=obj["description"],
                    pubdate=obj["pubdate"],
                    duration=obj["duration"],
                )
                for obj in data.get("result")
            ]
            return VideoSearchResponse(
                video_platform=VideoPlatform.BiliBili, video_list=video_list
            )
        except Exception as e:
            logger.exception(e)
            return VideoSearchResponse(
                video_platform=VideoPlatform.BiliBili, video_list=[]
            )


if __name__ == "__main__":
    from langchain_searxng.settings.settings import settings
    import asyncio

    v = VideoService(settings())

    async def main():
        print(
            await v.search_bilibli_video(
                VideoSearchRequest(query="北京", conversation_id="50")
            )
        )

    asyncio.run(main())
