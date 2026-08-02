from aiohttp import web
from sqlalchemy import select

from database.models import UserPet, Stats, Inventory, ShopItem
from database.database import async_session_maker
from services.pet_service import PetService
from services.shop_service import ShopService
from services.game_service import GameService
from services.achievement_service import AchievementService


class MiniAppAPI:
    def __init__(self):
        self.pet_service = PetService()
        self.shop_service = ShopService()
        self.game_service = GameService()
        self.achievement_service = AchievementService()

    async def get_pet_state(self, request: web.Request) -> web.Response:
        user_id = int(request.query.get('user_id'))

        pet = await self.pet_service.update_parameters(user_id)

        if not pet:
            pet = await self.pet_service.get_or_create_pet(user_id)

        return web.json_response({
            'pet_type': pet.pet_type.value if pet.pet_type else None,
            'stage': pet.stage.value,
            'xp': pet.xp,
            'hunger': pet.hunger,
            'happiness': pet.happiness,
            'hygiene': pet.hygiene,
            'energy': pet.energy,
            'discipline': pet.discipline,
            'strength': pet.strength
        })

    async def perform_action(self, request: web.Request) -> web.Response:
        data = await request.json()
        user_id = int(data['user_id'])
        action = data['action']

        if action == 'feed':
            result = await self.pet_service.feed_pet(user_id)
        elif action == 'play':
            result = await self.pet_service.play_with_pet(user_id)
        elif action == 'wash':
            result = await self.pet_service.wash_pet(user_id)
        elif action == 'sleep':
            result = await self.pet_service.sleep_pet(user_id)
        elif action == 'train':
            result = await self.pet_service.train_pet(user_id)
        else:
            return web.json_response({'success': False, 'message': 'Unknown action'}, status=400)

        return web.json_response(result)

    async def get_stats(self, request: web.Request) -> web.Response:
        user_id = int(request.query.get('user_id'))

        async with async_session_maker() as session:
            result = await session.execute(
                select(Stats).where(Stats.user_id == user_id)
            )
            stats = result.scalar_one_or_none()

            if not stats:
                return web.json_response({
                    'messages_sent': 0,
                    'games_played': 0,
                    'games_won': 0,
                    'win_streak': 0,
                    'feedings': 0,
                    'baths': 0,
                    'sleeps': 0,
                    'trainings': 0,
                    'login_streak': 0,
                    'currency': 0
                })

            return web.json_response({
                'messages_sent': stats.messages_sent,
                'games_played': stats.games_played,
                'games_won': stats.games_won,
                'win_streak': stats.win_streak,
                'feedings': stats.feedings,
                'baths': stats.baths,
                'sleeps': stats.sleeps,
                'trainings': stats.trainings,
                'login_streak': stats.login_streak,
                'currency': stats.currency
            })

    async def get_inventory(self, request: web.Request) -> web.Response:
        user_id = int(request.query.get('user_id'))

        async with async_session_maker() as session:
            result = await session.execute(
                select(Inventory, ShopItem)
                .join(ShopItem, Inventory.item_id == ShopItem.id)
                .where(Inventory.user_id == user_id)
            )
            items = result.all()

            inventory_data = []
            for inv, shop_item in items:
                inventory_data.append({
                    'id': inv.id,
                    'item_id': shop_item.id,
                    'name': shop_item.name,
                    'type': shop_item.item_type.value,
                    'quantity': inv.quantity,
                    'is_equipped': inv.is_equipped
                })

            return web.json_response({'items': inventory_data})

    async def get_shop_items(self, request: web.Request) -> web.Response:
        async with async_session_maker() as session:
            result = await session.execute(select(ShopItem))
            items = result.scalars().all()

            shop_data = []
            for item in items:
                shop_data.append({
                    'id': item.id,
                    'name': item.name,
                    'type': item.item_type.value,
                    'price': item.price,
                    'effect_type': item.effect_type,
                    'effect_value': item.effect_value,
                    'is_consumable': item.is_consumable
                })

            return web.json_response({'items': shop_data})

    async def buy_item(self, request: web.Request) -> web.Response:
        data = await request.json()
        user_id = int(data['user_id'])
        item_id = int(data['item_id'])

        result = await self.shop_service.buy_item(user_id, item_id)
        return web.json_response(result)

    async def use_item(self, request: web.Request) -> web.Response:
        data = await request.json()
        user_id = int(data['user_id'])
        inventory_id = int(data['inventory_id'])

        result = await self.shop_service.use_item(user_id, inventory_id)
        return web.json_response(result)

    async def equip_item(self, request: web.Request) -> web.Response:
        data = await request.json()
        user_id = int(data['user_id'])
        inventory_id = int(data['inventory_id'])

        result = await self.shop_service.equip_item(user_id, inventory_id)
        return web.json_response(result)

    async def play_phantom_cube(self, request: web.Request) -> web.Response:
        data = await request.json()
        user_id = int(data['user_id'])
        guess = int(data['guess'])

        result = await self.game_service.play_phantom_cube(user_id, guess)
        return web.json_response(result)

    async def play_number_whisper(self, request: web.Request) -> web.Response:
        data = await request.json()
        user_id = int(data['user_id'])
        guess = int(data['guess'])

        result = await self.game_service.play_number_whisper(user_id, guess)
        return web.json_response(result)

    async def play_cursed_riddle(self, request: web.Request) -> web.Response:
        data = await request.json()
        user_id = int(data['user_id'])
        answer = data['answer']

        result = await self.game_service.play_cursed_riddle(user_id, answer)
        return web.json_response(result)

    async def check_achievements(self, request: web.Request) -> web.Response:
        user_id = int(request.query.get('user_id'))

        newly_unlocked = await self.achievement_service.check_and_award_achievements(user_id)
        return web.json_response({'newly_unlocked': newly_unlocked})

    async def get_achievements(self, request: web.Request) -> web.Response:
        user_id = int(request.query.get('user_id'))

        achievements = await self.achievement_service.get_user_achievements(user_id)
        return web.json_response({'achievements': achievements})


def setup_routes(app: web.Application):
    api = MiniAppAPI()

    app.router.add_get('/api/pet', api.get_pet_state)
    app.router.add_post('/api/action', api.perform_action)
    app.router.add_get('/api/stats', api.get_stats)
    app.router.add_get('/api/inventory', api.get_inventory)
    app.router.add_get('/api/shop', api.get_shop_items)
    app.router.add_post('/api/shop/buy', api.buy_item)
    app.router.add_post('/api/shop/use', api.use_item)
    app.router.add_post('/api/shop/equip', api.equip_item)
    app.router.add_post('/api/game/phantom-cube', api.play_phantom_cube)
    app.router.add_post('/api/game/number-whisper', api.play_number_whisper)
    app.router.add_post('/api/game/cursed-riddle', api.play_cursed_riddle)
    app.router.add_get('/api/achievements/check', api.check_achievements)
    app.router.add_get('/api/achievements', api.get_achievements)
