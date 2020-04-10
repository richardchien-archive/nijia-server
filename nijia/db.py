from time import time
from typing import Optional, Dict, Any, List

import aiostream
from motor import motor_asyncio

from .log import logger

client: Optional[motor_asyncio.AsyncIOMotorClient] = None
db: Optional[motor_asyncio.AsyncIOMotorDatabase] = None
device_collection: Optional[motor_asyncio.AsyncIOMotorCollection] = None
history_state_collection: Optional[motor_asyncio.AsyncIOMotorCollection] = None


async def init(database_uri: str):
    global client, db, device_collection, history_state_collection
    client = motor_asyncio.AsyncIOMotorClient(database_uri)
    db = client.nijia
    device_collection = db.device
    history_state_collection = db.history_state
    logger.debug('database initialized')


async def find_device(uid: str) -> Optional[Dict[str, Any]]:
    """
    查找设备对象.

    Args:
        uid: 设备 UID

    Returns:
        设备对象.
    """
    return await device_collection.find_one({'uid': uid}, {"_id": 0})


async def find_all_devices() -> List[Dict[str, Any]]:
    """
    查找所有设备对象.

    Returns:
        设备对象的异步可迭代对象.
    """
    return await aiostream.stream.list(device_collection.find({}, {"_id": 0}))


async def insert_device(
        uid: str,
        name: str,
        model: str,
        switchable: bool,
        keep_history_state: bool, *,
        exist_ok: bool = False) -> Optional[Dict[str, Any]]:
    """
    插入设备对象.

    Args:
        uid: 设备 UID
        name: 设备名称
        model: 设备型号
        switchable: 是否可开关
        keep_history_state: 是否保留历史状态
        exist_ok: 是否允许该设备已存在

    Returns:
        已存在或刚插入的设备对象.
    """
    dev = await find_device(uid)
    if dev:
        logger.debug(f'device "{uid}" exists')
        return dev if exist_ok else None

    await device_collection.insert_one({
        'uid': uid,
        'name': name,
        'model': model,
        'switchable': switchable,
        'keep_history_state': keep_history_state,
        'state': {}
    })
    return await find_device(uid)


async def update_device_state(
        uid: str,
        state: Dict[str, Any],
        replace: bool = False) -> Optional[Dict[str, Any]]:
    """
    更新设备状态.

    Args:
        uid: 设备 UID
        state: 设备状态
        replace: 是否完整替换设备状态(若否, 则只更新 state 中给出的字段)

    Returns:
        设备对象.
    """
    # TODO: use findOneAndUpdate
    dev = await find_device(uid)
    if not dev:
        return None

    if replace:
        await device_collection.update_one(
            {'uid': uid},
            {'$set': {'state': state}}
        )
    else:
        await device_collection.update_one(
            {'uid': uid},
            {'$set': {f'state.{k}': v for k, v in state.items()}}
        )
    dev = await find_device(uid)
    if dev['keep_history_state']:
        await history_state_collection.insert_one({
            'device_uid': uid,
            'time': time(),
            'state': dev['state']
        })
    return dev


async def get_history_state_list(
        device_uid: str,
        count: int) -> List[Dict[str, Any]]:
    cursor = history_state_collection.find(
        {'device_uid': device_uid},
        {'_id': 0}
    )
    states = await cursor.sort('time', -1).to_list(length=count)
    states.reverse()
    return states
