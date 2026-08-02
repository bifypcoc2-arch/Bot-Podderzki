"""Разбор ошибок Telegram API.

Telegram не даёт машиночитаемых кодов для большинства случаев — только
текстовое description. Поэтому разбор по подстрокам — штатный способ.
Собрано в одном месте, чтобы не дублировать строки по сервисам.
"""


# Тема удалена или не существует.
_THREAD_MISSING_MARKERS = (
    "message thread not found",
    "topic_deleted",
    "topic deleted",
    "thread not found",
)

# Пользователь недоступен: заблокировал бота, удалил аккаунт или никогда не писал.
_USER_UNREACHABLE_MARKERS = (
    "bot was blocked by the user",
    "user is deactivated",
    "chat not found",
    "bot can't initiate conversation",
)


def _description(error: Exception) -> str:
    description = getattr(error, "description", None)
    return (description or str(error)).lower()


def is_thread_missing(error: Exception) -> bool:
    """Тема удалена в Telegram, хотя в базе ещё числится открытой."""
    return any(marker in _description(error) for marker in _THREAD_MISSING_MARKERS)


def is_user_unreachable(error: Exception) -> bool:
    """Писать этому пользователю бесполезно — повторять не надо."""
    return any(marker in _description(error) for marker in _USER_UNREACHABLE_MARKERS)
