import asyncio
from datetime import datetime
from typing import Literal, TypeVar, Generic, Sequence

from aredis_om import get_redis_connection, HashModel, Field
from core.redis import redis_conn as conn

T = TypeVar("T")

class ModelAdmin(HashModel, Generic[T]):

    @classmethod
    async def create(cls, ttl: int | None = None, **kwargs) -> T:
        model = cls(**kwargs)
        model = await model.save()
        if ttl:
            await model.expire(ttl)
        return model

    async def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        await self.save()

    async def delete(self) -> None:
        await super().delete(self.pk)

    @classmethod
    async def get(cls, pk: str) -> T | None:
        try:
            return await super().get(pk)
        except Exception:
            return None

    @classmethod
    async def filter(cls, **kwargs) -> Sequence[T]:
        conditions = [getattr(cls, key) == value for key, value in kwargs.items()]
        return await cls.find(*conditions).all()

    async def set_ttl(self, ttl: int) -> bool:
        return await self.expire(ttl)

    @classmethod
    async def all(cls):
        return await super().all_pks()


# Простая модель пользователя
class User(ModelAdmin):
    username: str = Field(index=True)
    email: str

    class Meta:
        database = conn


# Твоя модель сообщений ИИ
class MessageAI(ModelAdmin):

    kwork_id: int = Field(index=True)
    recipient_id: int = Field(index=True)
    sender: Literal['user', 'ai'] = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    class Meta:
        database = conn

    @classmethod
    async def delete_all_for_user(cls, user_id: int):
        msgs_by_kwork = await cls.filter(kwork_id=user_id)
        msgs_by_recipient = await cls.filter(recipient_id=user_id)
        all_msgs = {msg.pk: msg for msg in msgs_by_kwork}
        for msg in msgs_by_recipient:
            all_msgs[msg.pk] = msg
        for msg in all_msgs.values():
            await msg.delete()


async def main():

    from aredis_om.model import Migrator
    await Migrator().run()  # Создаем индексы

    # Создаем и сохраняем объекты
    user = User(username="virtudev", email="virtudev@example.com")
    await user.save()
    print(f"User saved with PK: {user.pk}")

    msg = await MessageAI.create(
        kwork_id=12345,
        recipient_id=67890,
        sender='user',
        content='Привет, бот!',
    )
    print(f"Message saved with PK: {msg.pk}")

    # Фильтруем по kwork_id
    msgs = await MessageAI.filter(kwork_id=12345)
    print(f"Found {len(msgs)} messages for kwork_id=12345")

asyncio.run(main())
