import json
from pydantic import BaseModel, ValidationError
from typing import Generic, TypeVar, Optional, Dict, Any
import requests
import logging
from model import SettingsModel, VideoSearchResponse
import sseclient

logger = logging.getLogger(__name__)
T = TypeVar("T")  # 泛型类型 T


class RespModel(BaseModel, Generic[T]):
    code: int
    msg: str
    data: T


# 将JSON字符串转换为 RespModel[具体类型] 类
def json_to_resp_model(json_str: str, data_type: T) -> RespModel[T]:
    data_dict = json.loads(json_str)
    resp_model_instance = RespModel[T](**data_dict, data=data_type(**data_dict["data"]))
    return resp_model_instance


class ApiRequest:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.timeout = 10 * 60  # 设置10分钟的超时

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        if headers:
            self.session.headers.update(headers)

        try:
            response = self.session.request(
                method, url, params=params, json=json_data, timeout=self.timeout
            )
            response.raise_for_status()  # 检查是否有请求错误
            return response.json()
        except requests.Timeout as timeout_error:
            # Handle timeout error
            logger.warning(
                f"Timeout error in {method} request to {url}: {timeout_error}"
            )
            raise
        except requests.RequestException as e:
            # Handle requests exceptions
            logger.warning(f"Error in {method} request to {url}: {e}")
            raise
        except Exception as e:
            # Handle other exceptions
            logger.warning(f"Unexpected error in {method} request to {url}: {e}")
            raise

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return self._request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return self._request("POST", endpoint, json_data=data, headers=headers)

    def close(self):
        self.session.close()


class SettingsApiHandler(ApiRequest):
    def __init__(self, base_url: str):
        super().__init__(base_url=base_url)

    def get_settings(
        self,
        endpoint: str = "/v1/config",
        headers: Optional[Dict[str, str]] = {},
    ) -> Any:
        try:
            resp_dict = self.get(endpoint=endpoint, headers=headers)
            logger.info(resp_dict)
            resp_model = RespModel[SettingsModel](**resp_dict)

            return resp_model

        except ValidationError as e:
            logger.warning(
                f"Unexpected ValidationError error in Settings request : {e}"
            )
            return None
        except Exception as e:
            logger.exception(f"Unexpected error in Settings request : {e}")
            return None


class SearchVideo(ApiRequest):
    def __init__(self, base_url: str):
        super().__init__(base_url=base_url)

    def search_video(
        self, endpoint: str, data: Any, headers: Optional[Dict[str, str]] = None
    ):
        try:
            resp_dict = self.post(endpoint=endpoint, data=data, headers=headers)
            logger.info(resp_dict)
            resp_model = RespModel[VideoSearchResponse](**resp_dict)

            return resp_model
        except Exception as e:
            logger.exception(f"Unexpected error in SearchVideo request : {e}")
            return None


class SearchSSE:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def with_requests(self, endpoint, data, headers):
        """Get a streaming response for the given event feed using requests."""
        import requests

        return requests.post(
            self.base_url + endpoint,
            json=data,
            stream=True,
            headers=headers,
        )

    def connect(
        self, endpoint: str, data: Any, headers: Optional[Dict[str, str]] = None
    ):
        try:
            response = self.with_requests(endpoint, data, headers)
            if response.status_code != 200:
                logger.warning(response.text)
                raise Exception(response.text)

            client = sseclient.SSEClient(response)
            for event in client.events():
                yield event

        except requests.RequestException as e:
            logger.warning(f"Error in SSE request to {endpoint}: {e}")
            raise
        except Exception as e:
            logger.exception(e)

    def close(self):
        self.session.close()


if __name__ == "__main__":
    base_url = "http://127.0.0.1:8002"
    endpoint = "/v2/search/sse"
    data = {
        "question": "中国旅游有哪些好玩的地点",
        "chat_history": [],
        "network": True,
        "conversation_id": "",
        "llm": "zhipuai",
    }
    headers = {
        "Accept": "text/event-stream; charset=utf-8",
        # "Authorization": f"Basic {Auth}",
    }

    sse_client = SearchSSE(base_url)
    sse_client.connect(endpoint, data, headers)
