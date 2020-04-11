import functools
from typing import Dict, Any

from . import rpc, db

service = rpc.Service()


@service.method
async def register(username: str, password: str):
    pass


@service.method
async def login(username: str, password: str) -> str:
    return 'token'


def require_auth(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # currently do nothing
        return func(*args, **kwargs)

    return wrapper


@service.method
@require_auth
async def get_device(uid: str):
    dev = await db.find_device(uid)
    if not dev:
        return rpc.ErrorResponse(
            rpc.ErrorCode.DATABASE_FAILED,
            '设备不存在或查找失败'
        )
    return dev


@service.method
@require_auth
async def get_device_list():
    devices = await db.find_all_devices()
    return devices


@service.method
@require_auth
async def get_history_state_list(device_uid: str, count: int = 20):
    states = await db.get_history_state_list(device_uid, count)
    return states


@service.method
@require_auth
async def update_device_state(uid: str, state: Dict[str, Any]):
    # TODO: 暂时直接更新数据库，以后应改为请求 gateway 控制设备
    dev = await db.update_device_state(uid, state, replace=False)
    if not dev:
        return rpc.ErrorResponse(
            rpc.ErrorCode.DATABASE_FAILED,
            '更新数据库字段失败'
        )
    return dev
