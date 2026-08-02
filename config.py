from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_url: str
    forum_group_id: int
    mini_app_url: str

    queue_wait_minutes: int = 5
    broadcast_timeout_minutes: int = 10
    broadcast_delay_ms: int = 50

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
