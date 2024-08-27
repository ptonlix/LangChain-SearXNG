import logging
from fastapi import APIRouter, Depends, Request
from typing import Dict, List
from langchain_searxng.server.utils.auth import authenticated
from langchain_searxng.server.utils.model import (
    RestfulModel,
    SystemErrorCode,
)
from langchain_searxng.settings.settings_loader import (
    get_active_settings,
    save_active_settings,
)


logger = logging.getLogger(__name__)

config_router_no_auth = APIRouter(prefix="/v1")

config_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])


@config_router_no_auth.get(
    "/config",
    response_model=RestfulModel[Dict],
    tags=["Config"],
)
async def get_config(request: Request) -> RestfulModel:

    try:
        return RestfulModel(data=get_active_settings())
    except Exception as e:
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)


@config_router.post(
    "/config",
    response_model=RestfulModel[None],
    tags=["Config"],
)
async def edit_config(request: Request, body: List[Dict]) -> RestfulModel:
    try:
        for profile, config in body.items():
            print(profile, config)
            save_active_settings(profile, config)

        return RestfulModel(data=None)
    except Exception as e:
        logger.exception(e)
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)
