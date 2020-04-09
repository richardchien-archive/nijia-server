import json
from typing import Dict, Any

from quart import Quart, request, jsonify, abort, websocket

from nijia import db, rpc, client_service, gateway_service
from nijia.log import logger

app = Quart(__name__)

rpc_services = {
    'client': client_service.service,
    'gateway': gateway_service.service,
}


async def handle_rpc_request(service: rpc.Service,
                             req_data: Dict[str, Any]) -> Dict[str, Any]:
    req = rpc.Request(
        method=req_data['method'],
        params=req_data['params'],
    )
    req_uid = req_data.get('uid')

    logger.debug('rpc request (uid = %s): %s', repr(req_uid), req)
    resp = (await service.invoke(req))
    logger.debug(f'rpc response (uid = %s): %s', repr(req_uid), resp)
    resp_data = resp.to_dict()
    resp_data['uid'] = req_uid
    return resp_data


@app.route('/<string:service_name>', methods=['POST'])
async def post(service_name: str):
    if service_name not in rpc_services:
        abort(404)

    return jsonify(await handle_rpc_request(
        rpc_services[service_name],
        await request.get_json()
    ))


@app.websocket('/ws/<string:service_name>')
async def ws(service_name: str):
    if service_name not in rpc_services:
        abort(404)

    while True:
        await websocket.send(json.dumps(await handle_rpc_request(
            rpc_services[service_name],
            json.loads(await websocket.receive())
        )))


@app.before_first_request
async def init_db():
    await db.init('mongodb://root:1qaz2wsx3edc@test.stdrc.cc:27017')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=6001, use_reloader=False)
