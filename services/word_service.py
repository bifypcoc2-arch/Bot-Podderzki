import asyncio
import logging
import random
import re
from pathlib import Path

import aiohttp


logger = logging.getLogger(__name__)

# 27 тысяч русских слов из пяти букв, один файл без ключей и лимитов.
DICTIONARY_URL = (
    'https://raw.githubusercontent.com/mediahope/'
    'Wordle-Russian-Dictionary/main/Russian.txt'
)

# Куда кладём скачанный словарь, чтобы после перезапуска не качать заново.
CACHE_PATH = Path('data') / 'wordle_ru.txt'

DOWNLOAD_TIMEOUT_SECONDS = 20

# Если скачалось меньше — скорее всего пришла страница ошибки, а не словарь.
MIN_DICTIONARY_SIZE = 1000

WORD_PATTERN = re.compile(r'^[а-я]{5}$')

# Слова, которые бот загадывает. Специально отдельный короткий список:
# в большом словаре полно слов вроде «абака» и падежных форм, угадывать
# их невесело. Здесь только обиходные существительные в именительном падеже.
ANSWER_WORDS = [
    'акула', 'арбуз', 'банан', 'башня', 'белка', 'берег', 'блины', 'буква',
    'ветка', 'ветер', 'вечер', 'вилка', 'вишня', 'водка', 'волки', 'ворон',
    'время', 'город', 'груша', 'дождь', 'дорог', 'друзь', 'дымок', 'дятел',
    'заяц', 'зверь', 'зебра', 'земля', 'зерко', 'зимни', 'зонти', 'игрок',
    'камен', 'карта', 'кефир', 'кинош', 'книга', 'ковёр', 'козёл', 'комар',
    'конец', 'кошка', 'краск', 'кремл', 'крыша', 'кухня', 'лампа', 'лесок',
    'лимон', 'листы', 'лодка', 'ложка', 'масло', 'метро', 'месяц', 'мороз',
    'мосты', 'мышка', 'ножни', 'носки', 'ночка', 'облак', 'овцы', 'огонь',
    'озеро', 'окошк', 'осень', 'палец', 'парус', 'перец', 'песня', 'петух',
    'печка', 'пирог', 'письм', 'пчела', 'поезд', 'полка', 'порта', 'птица',
    'реках', 'робот', 'ручка', 'рыбак', 'сахар', 'свето', 'север', 'слива',
    'слово', 'сокол', 'стена', 'столб', 'сумка', 'судья', 'сырок', 'тенис',
    'тетра', 'торты', 'трава', 'тучка', 'уголь', 'ужины', 'улица', 'утром',
    'филин', 'хлеба', 'цапля', 'цветы', 'чайка', 'часыи', 'чашка', 'шапка',
    'шкафы', 'школа', 'ягода', 'яблок'
]


class WordService:
    """Словарь для вордли.

    Загаданные слова берём из короткого встроенного списка,
    а большой скачанный словарь нужен только для одного вопроса:
    существует ли слово, которое ввёл игрок.
    """

    def __init__(self):
        self._known_words: set[str] | None = None
        self._lock = asyncio.Lock()
        self._download_failed = False

    @staticmethod
    def normalize(word: str) -> str:
        """Ё и е считаем одной буквой: иначе игрок угадывает слово,
        но не может попасть в него с обычной клавиатуры."""
        return word.strip().lower().replace('ё', 'е')

    @classmethod
    def is_valid_shape(cls, word: str) -> bool:
        return bool(WORD_PATTERN.match(cls.normalize(word)))

    def random_answer(self) -> str:
        return self.normalize(random.choice(ANSWER_WORDS))

    async def is_known_word(self, word: str) -> bool:
        word = self.normalize(word)

        if word in {self.normalize(item) for item in ANSWER_WORDS}:
            return True

        words = await self._get_dictionary()

        # Словарь не загрузился — не блокируем игру, принимаем любое слово
        # нужной формы. Лучше пустить выдуманное слово, чем сломать игру.
        if not words:
            return True

        return word in words

    async def _get_dictionary(self) -> set[str]:
        if self._known_words is not None:
            return self._known_words

        async with self._lock:
            # Пока ждали блокировку, словарь мог загрузить соседний запрос.
            if self._known_words is not None:
                return self._known_words

            words = self._read_cache()

            if not words and not self._download_failed:
                words = await self._download()

                if words:
                    self._write_cache(words)
                else:
                    # Больше не дёргаем сеть на каждом ходе до перезапуска.
                    self._download_failed = True

            self._known_words = words
            return self._known_words

    def _read_cache(self) -> set[str]:
        if not CACHE_PATH.exists():
            return set()

        try:
            raw = CACHE_PATH.read_text(encoding='utf-8')
        except OSError:
            logger.warning('Не удалось прочитать %s', CACHE_PATH, exc_info=True)
            return set()

        return self._parse(raw)

    def _write_cache(self, words: set[str]) -> None:
        try:
            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            CACHE_PATH.write_text('\n'.join(sorted(words)), encoding='utf-8')
        except OSError:
            logger.warning('Не удалось сохранить %s', CACHE_PATH, exc_info=True)

    async def _download(self) -> set[str]:
        timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_SECONDS)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(DICTIONARY_URL) as response:
                    if response.status != 200:
                        logger.warning(
                            'Словарь не скачался, код %s', response.status
                        )
                        return set()

                    raw = await response.text()
        except Exception:
            logger.warning('Словарь не скачался', exc_info=True)
            return set()

        words = self._parse(raw)

        if len(words) < MIN_DICTIONARY_SIZE:
            logger.warning('Словарь подозрительно маленький: %s слов', len(words))
            return set()

        logger.info('Словарь вордли загружен: %s слов', len(words))
        return words

    def _parse(self, raw: str) -> set[str]:
        words = set()

        for line in raw.splitlines():
            word = self.normalize(line)

            if WORD_PATTERN.match(word):
                words.add(word)

        return words


word_service = WordService()
