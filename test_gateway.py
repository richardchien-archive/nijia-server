import asyncio
import json
import random
import functools
from pprint import pprint
from typing import Callable, Dict, Any

import websockets

devices = [
    {
        'uid': '/box-1/led-1',
        'name': '吸顶灯',
        'model': '10000',
        'switchable': True,
    },
    {
        'uid': '/box-1/led-2',
        'name': '床头灯',
        'model': '10004',
        'switchable': True,
    },
    {
        'uid': '/box-1/temp-1',
        'name': '温湿度计',
        'model': '10001',
        'switchable': False,
    },
    {
        'uid': '/box-1/smoke-alarm-1',
        'name': '烟雾报警器',
        'model': '10003',
        'switchable': False,
    },
]

mock_state_generators = {}


def mock_state_gen(uid: str):
    def deco(func: Callable) -> Callable:
        mock_state_generators[uid] = func
        return func

    return deco


@mock_state_gen('/box-1/led-1')
async def gen_box_1_led_1(update):
    await update({'on': False})  # 启动时发送初始状态


@mock_state_gen('/box-1/led-2')
async def gen_box_1_led_2(update):
    await update({
        'on': True,
        'color': random.choice(['red', 'yellow', 'blue'])
    })


@mock_state_gen('/box-1/temp-1')
async def gen_box_1_temp_1(update):
    try:
        while True:
            temp = random.randint(100, 300) / 10.0
            hum = random.randint(10, 90)
            await update({'temperature': temp, 'humidity': hum})
            await asyncio.sleep(5)
    except Exception as e:
        pass


@mock_state_gen('/box-1/smoke-alarm-1')
async def gen_box_1_smoke_alarm_1(update):
    try:
        while True:
            alert = random.choices([True, False], [1, 2], k=1)[0]
            await update({'alert': alert})
            await asyncio.sleep(5)
    except Exception as e:
        pass


async def test():
    uri = 'ws://127.0.0.1:6001/ws/gateway'
    async with websockets.connect(uri) as websocket:
        async def update(uid: str, state: Dict[str, Any]):
            await websocket.send(json.dumps({
                'method': 'update_device_state',
                'params': {'uid': uid, 'state': state},
                'id': None,
            }))

        tasks = set()
        for dev in devices:
            await websocket.send(json.dumps({
                'method': 'register_device',
                'params': dev,
                'id': None,
            }))
            state_gen = mock_state_generators.get(dev['uid'])
            if state_gen:
                tasks.add(asyncio.create_task(
                    state_gen(functools.partial(update, dev['uid']))))

        async def receive():
            while True:
                pprint(json.loads(await websocket.recv()))

        await receive()


asyncio.get_event_loop().run_until_complete(test())
