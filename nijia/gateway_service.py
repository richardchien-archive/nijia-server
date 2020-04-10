from typing import Dict, Any

from . import rpc, db

service = rpc.Service()


@service.method
async def register_device(uid: str,
                          name: str,
                          model: str,
                          switchable: bool,
                          keep_history_state: bool):
    dev = await db.insert_device(
        uid,
        name,
        model,
        switchable,
        keep_history_state,
        exist_ok=True
    )
    if not dev:
        return rpc.ErrorResponse(
            rpc.ErrorCode.DATABASE_FAILED,
            '插入数据库失败'
        )
    return dev


@service.method
async def update_device_state(uid: str, state: Dict[str, Any]):
    dev = await db.update_device_state(uid, state, replace=True)
    if not dev:
        return rpc.ErrorResponse(
            rpc.ErrorCode.DATABASE_FAILED,
            '更新数据库字段失败'
        )
    return dev
