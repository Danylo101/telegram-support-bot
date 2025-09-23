from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int
    OPERATOR_IDS: List[int] = []
    MONGO_USERNAME: str
    MONGO_PASSWORD: str
    MONGO_HOST: str
    MONGO_HOST_EXTERNAL: str
    MONGO_PORT: int
    MONGO_PORT_EXTERNAL: int
    MONGO_DB_NAME: str
    MONGO_DB_ROOT_NAME: str

    model_config = SettingsConfigDict(env_file="../.env")


settings = Settings()