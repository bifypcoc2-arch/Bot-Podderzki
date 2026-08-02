import asyncio
import os
from aiohttp import web
from api.miniapp_api import setup_routes
from database.database import init_db


async def init_app():
    app = web.Application()

    await init_db()

    setup_routes(app)

    miniapp_path = os.path.join(os.path.dirname(__file__), 'miniapp')
    app.router.add_static('/', miniapp_path, name='static', show_index=True)

    return app


if __name__ == '__main__':
    app = asyncio.run(init_app())
    print("Mini App запущен на http://localhost:8080")
    print("Откройте в браузере: http://localhost:8080")
    web.run_app(app, host='localhost', port=8080)
