from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    TELEGRAM_BOT_TOKEN: str

    BINGX_API_KEY: str
    BINGX_API_SECRET: str


settings = Settings()
