from typing import Literal

from pydantic import BaseModel, Field

from langchain_searxng.settings.settings_loader import load_active_settings


class CorsSettings(BaseModel):
    """CORS configuration.

    For more details on the CORS configuration, see:
    # * https://fastapi.tiangolo.com/tutorial/cors/
    # * https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
    """

    enabled: bool = Field(
        description="Flag indicating if CORS headers are set or not."
        "If set to True, the CORS headers will be set to allow all origins, methods and headers.",
        default=False,
    )
    allow_credentials: bool = Field(
        description="Indicate that cookies should be supported for cross-origin requests",
        default=False,
    )
    allow_origins: list[str] = Field(
        description="A list of origins that should be permitted to make cross-origin requests.",
        default=[],
    )
    allow_origin_regex: list[str] = Field(
        description="A regex string to match against origins that should be permitted to make cross-origin requests.",
        default=None,
    )
    allow_methods: list[str] = Field(
        description="A list of HTTP methods that should be allowed for cross-origin requests.",
        default=[
            "GET",
        ],
    )
    allow_headers: list[str] = Field(
        description="A list of HTTP request headers that should be supported for cross-origin requests.",
        default=[],
    )


class AuthSettings(BaseModel):
    """Authentication configuration.

    The implementation of the authentication strategy must
    """

    enabled: bool = Field(
        description="Flag indicating if authentication is enabled or not.",
        default=False,
    )
    secret: str = Field(
        description="The secret to be used for authentication. "
        "It can be any non-blank string. For HTTP basic authentication, "
        "this value should be the whole 'Authorization' header that is expected"
    )


class ServerSettings(BaseModel):
    env_name: str = Field(
        description="Name of the environment (prod, staging, local...)"
    )
    port: int = Field(
        description="Port of Langchain-DeepRead FastAPI server, defaults to 8001"
    )
    cors: CorsSettings = Field(
        description="CORS configuration", default=CorsSettings(enabled=False)
    )
    auth: AuthSettings = Field(
        description="Authentication configuration",
        default_factory=lambda: AuthSettings(enabled=False, secret="secret-key"),
    )


class LLMSettings(BaseModel):
    mode: Literal["local", "openai", "zhipuai", "all", "mock"]
    max_new_tokens: int = Field(
        256,
        description="The maximum number of token that the LLM is authorized to generate in one completion.",
    )


class EmbeddingSettings(BaseModel):
    mode: Literal["local", "openai", "zhipuai", "zhipuwebsearch", "mock"]


class OpenAISettings(BaseModel):
    temperature: float
    modelname: str
    api_key: str
    api_base: str


class DeepSeekSettings(BaseModel):
    temperature: float
    modelname: str
    api_key: str
    api_base: str


class ZhipuAISettings(BaseModel):
    temperature: float
    top_p: float
    modelname: str
    api_key: str
    api_base: str


class LangSmithSettings(BaseModel):
    trace_version_v2: bool
    langchain_project: str
    api_key: str


class SearXNGSettings(BaseModel):
    host: str
    language: str
    safesearch: int
    categories: str
    engines: list[str]
    num_results: int


class Settings(BaseModel):
    server: ServerSettings
    llm: LLMSettings
    embedding: EmbeddingSettings
    openai: OpenAISettings
    deepseek: DeepSeekSettings
    zhipuai: ZhipuAISettings
    langsmith: LangSmithSettings
    searxng: SearXNGSettings


"""
This is visible just for DI or testing purposes.

Use dependency injection or `settings()` method instead.
"""
unsafe_settings = load_active_settings()

"""
This is visible just for DI or testing purposes.

Use dependency injection or `settings()` method instead.
"""
unsafe_typed_settings = Settings(**unsafe_settings)


def settings() -> Settings:
    """Get the current loaded settings from the DI container.

    This method exists to keep compatibility with the existing code,
    that require global access to the settings.

    For regular components use dependency injection instead.
    """
    from langchain_searxng.di import global_injector

    return global_injector.get(Settings)
