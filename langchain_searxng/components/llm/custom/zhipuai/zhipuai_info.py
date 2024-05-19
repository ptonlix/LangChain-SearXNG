"""Callback Handler that prints to std out."""

import threading
from typing import Any, Dict, List

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from contextlib import contextmanager
from typing import (
    Generator,
    cast,
)
from langchain_core.outputs import (
    ChatGenerationChunk,
)

MODEL_COST_PER_1K_TOKENS = {
    # input
    "glm-4": 0.1,
    "glm-3-turbo": 0.005,
    # output
    "glm-4-completion": 0.1,
    "glm-3-turbo-completion": 0.005,
}


def standardize_model_name(
    model_name: str,
    is_completion: bool = False,
) -> str:
    """
    Standardize the model name to a format that can be used in the ZhipuAI API.

    Args:
        model_name: Model name to standardize.
        is_completion: Whether the model is used for completion or not.
            Defaults to False.

    Returns:
        Standardized model name.

    """
    model_name = model_name.lower()
    if is_completion and (
        model_name.startswith("glm-4") or model_name.startswith("glm-3-turbo")
    ):
        return model_name + "-completion"
    else:
        return model_name


def get_zhipuai_token_cost_for_model(
    model_name: str, num_tokens: int, is_completion: bool = False
) -> float:
    """
    Get the cost in USD for a given model and number of tokens.

    Args:
        model_name: Name of the model
        num_tokens: Number of tokens.
        is_completion: Whether the model is used for completion or not.
            Defaults to False.

    Returns:
        Cost in CNY.
    """
    model_name = standardize_model_name(model_name, is_completion=is_completion)
    if model_name not in MODEL_COST_PER_1K_TOKENS:
        raise ValueError(
            f"Unknown model: {model_name}. Please provide a valid ZhipuAI model name."
            "Known models are: " + ", ".join(MODEL_COST_PER_1K_TOKENS.keys())
        )
    return MODEL_COST_PER_1K_TOKENS[model_name] * (num_tokens / 1000)


class ZhipuAICallbackHandler(BaseCallbackHandler):
    """Callback Handler that tracks ZhipuAI info."""

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    successful_requests: int = 0
    total_cost: float = 0.0

    web_search: List[Dict[str, str]] = []

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return (
            f"Tokens Used: {self.total_tokens}\n"
            f"\tPrompt Tokens: {self.prompt_tokens}\n"
            f"\tCompletion Tokens: {self.completion_tokens}\n"
            f"Successful Requests: {self.successful_requests}\n"
            f"Total Cost (CNY): ${self.total_cost}"
        )

    @property
    def always_verbose(self) -> bool:
        """Whether to call verbose callbacks even if verbose is False."""
        return True

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Print out the prompts."""
        pass

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Print out the token."""
        chunk = cast(ChatGenerationChunk, kwargs.get("chunk"))
        web_search = chunk.message.response_metadata.get("web_search")
        usage = chunk.message.response_metadata.get("usage")
        if usage:
            self.total_tokens = usage.get("total_tokens", 0)
            self.prompt_tokens = usage.get("prompt_tokens", 0)
            self.completion_tokens = usage.get("completion_tokens", 0)

            model_name = standardize_model_name(kwargs.get("model_name", ""))
            if model_name in MODEL_COST_PER_1K_TOKENS:
                completion_cost = get_zhipuai_token_cost_for_model(
                    model_name, self.completion_tokens, is_completion=True
                )
                prompt_cost = get_zhipuai_token_cost_for_model(
                    model_name, self.prompt_tokens
                )
            else:
                completion_cost = 0
                prompt_cost = 0
            self.total_cost += prompt_cost + completion_cost
        if web_search:
            self.web_search = web_search
        pass

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Collect token usage."""
        if response.llm_output is None:
            return None

        if "token_usage" not in response.llm_output:
            with self._lock:
                self.successful_requests += 1
            return None

        # compute tokens and cost for this request
        token_usage = response.llm_output["token_usage"]
        completion_tokens = token_usage.get("completion_tokens", 0)
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        model_name = standardize_model_name(response.llm_output.get("model_name", ""))
        if model_name in MODEL_COST_PER_1K_TOKENS:
            completion_cost = get_zhipuai_token_cost_for_model(
                model_name, completion_tokens, is_completion=True
            )
            prompt_cost = get_zhipuai_token_cost_for_model(model_name, prompt_tokens)
        else:
            completion_cost = 0
            prompt_cost = 0
        web_search = response.llm_output.get("web_search")
        # update shared state behind lock
        with self._lock:
            self.total_cost += prompt_cost + completion_cost
            self.total_tokens += token_usage.get("total_tokens", 0)
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            self.successful_requests += 1
            self.web_search = web_search

    def __copy__(self) -> "ZhipuAICallbackHandler":
        """Return a copy of the callback handler."""
        return self

    def __deepcopy__(self, memo: Any) -> "ZhipuAICallbackHandler":
        """Return a deep copy of the callback handler."""
        return self


@contextmanager
def get_zhipuai_callback() -> Generator[ZhipuAICallbackHandler, None, None]:
    """Get the ZhipuAI callback handler in a context manager.
    which conveniently exposes token and cost information.

    Returns:
        ZhipuAICallbackHandler: The ZhipuAI callback handler.

    Example:
        >>> with get_zhipuai_callback() as cb:
        ...     # Use the ZhipuAI callback handler
    """
    cb = ZhipuAICallbackHandler()
    yield cb
