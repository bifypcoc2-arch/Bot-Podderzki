# Структура проекта

## Общая архитектура

```
┌─────────────────┐
│  Telegram User  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Telegram Bot   │◄────►│   Database   │
│   (main.py)     │      │   (SQLite)   │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│  Forum Topics   │
│   (Support)     │
└─────────────────┘

         +

┌─────────────────┐      ┌──────────────┐
│   Mini App      │◄────►│  Web Server  │
│  (HTML/JS/CSS)  │      │ (aiohttp)    │
└─────────────────┘      └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   Database   │
                         │   (SQLite)   │
                         └──────────────┘
```

## Модули и их назначение

### Основные файлы
- `main.py` - Точка входа бота, инициализация и регистрация handlers
- `web_server.py` - Веб-сервер для Mini App API
- `config.py` - Управление конфигурацией через pydantic-settings
- `init_db.py` - Инициализация БД и заполнение начальными данными
- `add_admin.py` - Утилита для добавления администраторов
- `check_db.py` - Утилита для проверки состояния БД

### Database (`database/`)
- `database.py` - Настройка SQLAlchemy async engine
- `models.py` - ORM модели для всех таблиц

#### Основные модели:
- **User** - Пользователи бота
- **Admin** - Администраторы с ролями
- **Topic** - Темы поддержки в форуме
- **Broadcast** - Рассылки
- **UserPet** - Питомцы пользователей
- **ShopItem** - Товары в магазине
- **Inventory** - Инвентарь пользователей
- **Achievement** - Достижения
- **Stats** - Статистика пользователей

### Handlers (`handlers/`)
Обработчики команд и сообщений бота.

- `support.py` - Пользовательская поддержка
  - `/start` - Приветствие
  - Пересылка сообщений в форум-топики
  
- `admin.py` - Административные команды
  - `/spec` - Перевод темы в режим SPEC
  - `/unspec` - Снятие режима SPEC
  - Фильтрация сообщений в SPEC-темах
  
- `broadcast.py` - Система рассылок
  - `/ad` - Создание рассылки
  - `/ads` - Управление рассылками
  - Редактирование, отправка, удаление
  
- `miniapp.py` - Интеграция Mini App
  - `/pet` - Открытие мини-приложения

### Services (`services/`)
Бизнес-логика приложения.

- `support_service.py` - Логика поддержки
  - Создание пользователей
  - Создание/получение топиков
  - Пересылка сообщений
  
- `admin_service.py` - Логика администрирования
  - Проверка ролей
  - Управление SPEC-режимом
  - Фильтрация доступа
  
- `broadcast_service.py` - Логика рассылок
  - CRUD рассылок
  - Отправка сообщений с задержками
  - Обработка ошибок доставки
  
- `pet_service.py` - Логика питомцев
  - Создание питомцев
  - Обновление параметров
  - Действия (кормить, играть, etc.)
  - Система роста и эволюции

### API (`api/`)
REST API для Mini App.

- `miniapp_api.py` - Endpoints для фронтенда
  - `GET /api/pet` - Состояние питомца
  - `POST /api/action` - Выполнение действия
  - `GET /api/stats` - Статистика пользователя
  - `GET /api/inventory` - Инвентарь
  - `GET /api/shop` - Магазин

### Mini App (`miniapp/`)
Frontend приложение.

- `index.html` - HTML структура
- `app.js` - JavaScript логика
  - Загрузка данных питомца
  - Выполнение действий
  - Навигация между разделами
  - Обновление UI
- `styles.css` - Стилизация интерфейса

### Filters (`filters/`)
Фильтры для обработки сообщений.

- `role_filter.py` - Проверка уровня доступа администратора

## Поток данных

### Пользовательское сообщение:
```
User → Bot → support_service → Database (User, Topic)
                ↓
          Forward to Forum Topic
```

### Ответ администратора:
```
Admin Reply in Topic → Bot → Check if SPEC mode
                         ↓
                   Check admin level
                         ↓
                   Forward to User or Delete
```

### Действие с питомцем:
```
Mini App → POST /api/action → pet_service → Database (UserPet, Stats)
                                  ↓
                            Update parameters
                                  ↓
                            Return new state → Mini App
```

### Рассылка:
```
/ad → FSM: waiting_content → save draft → Database
                                            ↓
/ads → select draft → edit/send/delete
                         ↓
                    send → iterate users → send with delay
                                            ↓
                                       update stats
```

## Система ролей

Уровни доступа (роль → level):
- ADMIN → 1 (базовый доступ)
- SPEC_ADMIN → 2 (доступ к SPEC-темам)
- SENIOR_ADMIN → 3 (доступ к SPEC-темам)
- TECH_ADMIN → 4 (доступ к рассылкам)
- OWNER → 5 (полный доступ)

Проверка: `admin.role_level >= required_level`

## Система питомцев

### Параметры (0-100):
- hunger - голод
- happiness - счастье
- hygiene - гигиена
- energy - энергия
- discipline - дисциплина
- strength - лапки (влияет на игры)

### Действия и эффекты:
- feed → +hunger, +xp
- play → +happiness, +xp
- wash → +hygiene, +xp
- sleep → +energy, +xp (требует energy < 100)
- train → -energy, +discipline, +strength, +xp

### Рост питомца:
```
Зарождение (10 XP) → Яйцо (50 XP) → Малыш (150 XP) → Подросток (300 XP) → Взрослый
                                        ↑
                                  Выбор вида (случайно)
```

Условие роста: XP >= threshold И все параметры >= 60%

## Безопасность

- Проверка роли на каждое действие (не кешируется)
- FSM для многошаговых действий (рассылки)
- Задержка между сообщениями в рассылке (анти-спам)
- Валидация входных данных через pydantic
- Обработка ошибок при отправке сообщений
