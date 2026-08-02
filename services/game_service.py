import random
from sqlalchemy import select

from database.models import UserPet, Stats
from database.database import async_session_maker


class GameService:
    BASE_WIN_CHANCE = 0.4
    STRENGTH_WIN_BONUS = 0.006

    WIN_REWARD = 50
    LOSS_REWARD = 10

    async def play_phantom_cube(self, user_id: int, guess: int) -> dict:
        """
        Призрачный куб - угадай число от 1 до 6
        """
        if guess < 1 or guess > 6:
            return {"success": False, "message": "Число должно быть от 1 до 6"}

        async with async_session_maker() as session:
            pet_result = await session.execute(
                select(UserPet).where(UserPet.user_id == user_id)
            )
            pet = pet_result.scalar_one_or_none()

            if not pet:
                return {"success": False, "message": "Питомец не найден"}

            win_chance = self._calculate_win_chance(pet.strength)

            roll = random.randint(1, 6)
            won = (guess == roll) or (random.random() < win_chance)

            reward = self.WIN_REWARD if won else self.LOSS_REWARD

            stats = await self._get_stats(session, user_id)
            stats.games_played += 1
            stats.currency += reward

            if won:
                stats.games_won += 1
                stats.win_streak += 1
            else:
                stats.win_streak = 0

            await session.commit()

            return {
                "success": True,
                "won": won,
                "roll": roll,
                "guess": guess,
                "reward": reward,
                "currency": stats.currency,
                "win_streak": stats.win_streak
            }

    async def play_number_whisper(self, user_id: int, guess: int) -> dict:
        """
        Шёпот цифр - угадай число от 1 до 10
        """
        if guess < 1 or guess > 10:
            return {"success": False, "message": "Число должно быть от 1 до 10"}

        async with async_session_maker() as session:
            pet_result = await session.execute(
                select(UserPet).where(UserPet.user_id == user_id)
            )
            pet = pet_result.scalar_one_or_none()

            if not pet:
                return {"success": False, "message": "Питомец не найден"}

            win_chance = self._calculate_win_chance(pet.strength)

            secret_number = random.randint(1, 10)
            distance = abs(guess - secret_number)

            won = (distance == 0) or (distance <= 2 and random.random() < win_chance)

            reward = self.WIN_REWARD if won else self.LOSS_REWARD

            stats = await self._get_stats(session, user_id)
            stats.games_played += 1
            stats.currency += reward

            if won:
                stats.games_won += 1
                stats.win_streak += 1
            else:
                stats.win_streak = 0

            await session.commit()

            return {
                "success": True,
                "won": won,
                "secret_number": secret_number,
                "guess": guess,
                "distance": distance,
                "reward": reward,
                "currency": stats.currency,
                "win_streak": stats.win_streak
            }

    async def play_cursed_riddle(self, user_id: int, answer: str) -> dict:
        """
        Проклятая загадка - выбери один из трёх вариантов
        """
        valid_answers = ["A", "B", "C"]
        answer = answer.upper()

        if answer not in valid_answers:
            return {"success": False, "message": "Ответ должен быть A, B или C"}

        async with async_session_maker() as session:
            pet_result = await session.execute(
                select(UserPet).where(UserPet.user_id == user_id)
            )
            pet = pet_result.scalar_one_or_none()

            if not pet:
                return {"success": False, "message": "Питомец не найден"}

            win_chance = self._calculate_win_chance(pet.strength)

            correct_answer = random.choice(valid_answers)
            won = (answer == correct_answer) or (random.random() < win_chance * 0.5)

            reward = self.WIN_REWARD if won else self.LOSS_REWARD

            stats = await self._get_stats(session, user_id)
            stats.games_played += 1
            stats.currency += reward

            if won:
                stats.games_won += 1
                stats.win_streak += 1
            else:
                stats.win_streak = 0

            await session.commit()

            return {
                "success": True,
                "won": won,
                "correct_answer": correct_answer,
                "your_answer": answer,
                "reward": reward,
                "currency": stats.currency,
                "win_streak": stats.win_streak
            }

    def _calculate_win_chance(self, strength: int) -> float:
        """Розраховує шанс виграшу на основі параметру strength"""
        return min(0.9, self.BASE_WIN_CHANCE + (strength * self.STRENGTH_WIN_BONUS))

    async def _get_stats(self, session, user_id: int) -> Stats:
        result = await session.execute(
            select(Stats).where(Stats.user_id == user_id)
        )
        stats = result.scalar_one_or_none()

        if not stats:
            stats = Stats(user_id=user_id)
            session.add(stats)

        return stats
