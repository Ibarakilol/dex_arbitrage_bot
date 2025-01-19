from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    VOLUME: int = 1000
    VOLUMES: list[int] = [100, 200, 300, 500, 1000, 2000, 3000, 5000, 10000]
    MIN_PROFIT: int = 5
    BLACK_LIST: list[str] = []

    BINGX_API_KEY: str
    BINGX_API_SECRET: str

    COINEX_API_KEY: str
    COINEX_API_SECRET: str


settings = Settings()
