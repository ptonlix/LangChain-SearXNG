from pydantic import BaseModel
from typing import Generic, TypeVar


T = TypeVar("T")  # 泛型类型 T


class RestfulModel(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: T


"""
Server Error Code List

"""

"""
system:     10000-10099
"""
SystemErrorCode = 10001

"""
search:     10100-10199
"""
ChatHistoryTooLong = 10100
