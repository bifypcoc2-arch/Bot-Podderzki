# Telegram Bot - Поддержка с питомцами

## Быстрый старт

### 1. Установка
```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```         
### 2. Настройка
```bash
# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать .env своими данными
```

### 3. Инициализация
```bash
# Создать базу данных и заполнить начальными данными
python init_db.py

# Добавить первого администратора (замените ID)
python add_admin.py 123456789 OWNER 5
```

### 4. Запуск
```bash
# Linux/Mac
chmod +x start.sh
./start.sh

# Windows
start.bat

# Или вручную в двух терминалах
python main.py
python web_server.py
```

## Структура команд

### Пользовательские команды
- `/start` - Начать работу с ботом
- `/pet` - Открыть питомца

### Админские команды
- `/spec` - Режим спец-доступа (уровень 3+)
- `/unspec` - Снять спец-режим (уровень 3+)
- `/ad` - Создать рассылку (уровень 4+)
- `/ads` - Управление рассылками (уровень 4+)

## API Endpoints

- `GET /api/pet?user_id={id}` - Состояние питомца
- `POST /api/action` - Действие с питомцем
- `GET /api/stats?user_id={id}` - Статистика
- `GET /api/inventory?user_id={id}` - Инвентарь
- `GET /api/shop` - Магазин

## Troubleshooting

**База данных не создаётся**
```bash
python init_db.py
```

**Бот не отвечает**
- Проверьте BOT_TOKEN в .env
- Проверьте интернет-соединение
- Проверьте логи в консоли

**Mini App не загружается**
- Проверьте MINI_APP_URL в .env
- Убедитесь что web_server.py запущен
- Проверьте что URL доступен через HTTPS

## Дальнейшая разработка

См. полный README.md для деталей архитектуры и roadmap.
