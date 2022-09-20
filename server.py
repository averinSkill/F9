import os

from aiohttp import web


WS_FILE = 'websocket.html'


async def wshandler(request: web.Request):
    resp = web.WebSocketResponse(autoping=True, heartbeat=5)
    available = resp.can_prepare(request)
    if not available:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    await resp.prepare(request)

    await resp.send_str("Welcome!!!")

    try:
        print("Someone joined.")
        for ws in request.app["sockets"]:
            await ws.send_str("Someone joined")
        request.app["sockets"].append(resp)

        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                print("Пришла месага: ", msg.data)
                if msg.data == "--heartbeat--":
                    await resp.send_str("--heartbeat--")
                else:
                    for ws in request.app["sockets"]:
                        if ws is not resp:
                            await ws.send_str(msg.data)
            else:
                return resp
        return resp

    finally:
        request.app["sockets"].remove(resp)
        print("Someone disconnected.")
        for ws in request.app["sockets"]:
            await ws.send_str("Someone disconnected.")


async def on_shutdown(app: web.Application):
    for ws in app["sockets"]:
        await ws.close()


def init():
    app = web.Application()
    app["sockets"] = []
    app.add_routes([web.get("/", wshandler)]) # wshandler опишем позже
    app.on_shutdown.append(on_shutdown) # on_shutdown опишем позже
    return app


web.run_app(init())