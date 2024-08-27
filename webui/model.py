from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class Embedding(BaseModel):
    """向量模型"""

    mode: str


class Langsmith(BaseModel):
    """调试配置"""

    """LangSmith API KEY"""
    api_key: str
    """版本V2 是否打开"""
    trace_version_v2: bool


class Llm(BaseModel):
    """大语言模型"""

    mode: str


class Openai(BaseModel):
    """openai配置"""

    """api请求地址"""
    api_base: str
    """API_KEY"""
    api_key: str
    """模型名称"""
    modelname: str
    """温度配置"""
    temperature: int


class Searxng(BaseModel):
    """搜索引擎配置"""

    """搜索分类"""
    categories: str
    """搜索引擎"""
    # engines: Annotated[List[str], Field(
    #     description="Upload a profile picture, must not be more than 16kb"
    # )]
    """搜索引擎地址"""
    host: str
    """搜索语言"""
    language: str
    """搜索结果"""
    num_results: int
    """安全等级"""
    safesearch: int


class PurpleAuth(BaseModel):
    """认证配置"""

    """是否开启认证"""
    enabled: bool
    """认证密钥"""
    secret: str


class PurpleCors(BaseModel):
    """跨域配置"""

    allow_headers: List[str]
    """跨域配置"""
    allow_methods: List[str]
    allow_origins: List[str]
    """是否开启跨域"""
    enabled: bool


class Server(BaseModel):
    """服务器配置"""

    """认证配置"""
    auth: PurpleAuth
    cors: PurpleCors
    env_name: str
    """服务器端口（前端不可修改）"""
    port: int


class Zhipuai(BaseModel):
    """智谱模型配置"""

    """API KEY"""
    api_key: str
    """模型名称"""
    modelname: str
    """温度"""
    temperature: float
    """top_p"""
    top_p: float


class Settings(BaseModel):
    """向量模型"""

    name: str = None
    embedding: Embedding
    """搜索引擎配置"""
    searxng: Searxng
    """大语言模型"""
    llm: Llm
    """openai配置"""
    openai: Openai
    """服务器配置"""
    # server: Server
    """智谱模型配置"""
    zhipuai: Zhipuai
    """调试配置"""
    langsmith: Langsmith


class SettingsModel(BaseModel):
    default: Optional[Settings] = None
    pro: Optional[Settings] = None


class VideoSearchResult(BaseModel):
    """视频搜索结果"""

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


class Response(BaseModel):
    code: int
    data: List[Settings]
    msg: str
