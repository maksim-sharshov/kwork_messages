from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings
from aiogram.types import BotCommand
from google.oauth2 import service_account


class PostgresConfig(BaseSettings):
    NAME: str
    HOST: str
    PORT: int
    PASSWORD: str
    USER: str

    @property
    def URL(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    class Config:
        env_prefix = 'POSTGRES_'
        env_file = '.env'
        extra = 'ignore'


class GptConfig(BaseSettings):
    TOKEN: str
    
    class Config:
        env_prefix = 'OPENAI_'
        env_file = '.env'
        extra = 'ignore'


class BotConfig(BaseSettings):
    TOKEN: str
    CHAT_ID: int
    COMMANDS: list[BotCommand] = [
        BotCommand(
            command='start',
            description='Запустить бота'
        )
    ]
    MANAGER_COMMANDS: list[BotCommand] = [
        BotCommand(
            command='project',
            description='Последний актуальный проект'
        )
    ]

    class Config:
        env_prefix = 'BOT_'
        env_file = '.env'
        extra = 'ignore'


# class OtaskConfig(BaseSettings):
#     WS_SLUG: str
#     PASSWORD: str
#     EMAIL: str
#
#     class Config:
#         env_prefix = 'OTASK_'
#         env_file = '.env'
#         extra = 'ignore'

class Settings:
    postgres = PostgresConfig()
    bot = BotConfig()
    openai = GptConfig()

settings = Settings()
