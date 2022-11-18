import os
from aiohttp import web


WS_FILE = os.path.join(os.path.dirname(__file__), 'websocket.html')


async def wshandler(request: web.Request):
    resp = web.WebSocketResponse()  #  Для начала создаём объект HTTP-ответа
    available = resp.can_prepare(request)  #  Проверяем, можем ли ответить сразу в запрос, а такое возможно, только если используется веб-сокет.
    if not available:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    await resp.prepare(request)  #  открываем соединение через веб-сокеты, ведь мы это можем.

    await resp.send_str("Welcome!!!")  #  шлём приветственное сообщение

    try:
        print("Someone joined.")
        #   отослаем всем пользователям, что у нас новый пользователь
        for ws in request.app["sockets"]:
            await ws.send_str("Someone joined")
        request.app["sockets"].append(resp)
        #   Далее мы начинаем перебирать сообщения, которые пришли от пользователя
        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                for ws in request.app["sockets"]:
                    if ws is not resp:
                        await ws.send_str(msg.data)
            else:
                return resp
        return resp
# Обратите внимание, что resp не содержит все сообщения, которые пользователь переслал,
# а передает их по одному через асинхронный вариант for цикла.
# То есть resp представляет собой итератор, который отдаёт сообщения по одному, когда они приходят.
# А когда их нет, то выполнение программы передаётся в Event Loop, который и следит за приходящими сообщениями.
# Когда же пользователь отключается, то выполнение цикла завершается,
# а выполнение функции продолжается, и мы попадаем в блок finally

    finally:
        #  Мы удаляем соединение из списка, а всем пользователям сообщаем, что пользователь отключился
        request.app["sockets"].remove(resp)
        print("Someone disconnected.")
        for ws in request.app["sockets"]:
            await ws.send_str("Someone disconnected.")

# По сути, мы здесь просто передаём всем клиентам, что соединение закрылось.
# Список app["sockets"] очищать не нужно, ведь больше мы его использовать не будем, а память и без нас очистится

async def on_shutdown(app: web.Application):
    for ws in app["sockets"]:
        await ws.close()



def init():
    app = web.Application() #  Тут мы импортировали модуль web из библиотеки aiohttp и используем его для создания экземпляра приложения.
    app["sockets"] = []     #  В приложении мы сохраняем список app["sockets"] для хранения всех соединений.
    app.router.add_get("/", wshandler) # Добавляет обработчик для GET-запросов по пути "/".
    app.on_shutdown.append(on_shutdown) # Отключение от приложения
    return app


web.run_app(init()) #  Передаем созданное приложение в web.run_app — именно там будет выполняться Event Loop.
