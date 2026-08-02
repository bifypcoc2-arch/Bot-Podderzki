import asyncio
from aiohttp import web

from api.miniapp_api import setup_routes
from database.database import init_db
from config import settings


async def init_app():
    await init_db()

    app = web.Application()
    setup_routes(app)

    app.router.add_static('/miniapp', 'miniapp', name='miniapp')

    return app


def main():
    app = asyncio.run(init_app())
    web.run_app(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
