from datetime import datetime
from typing import Literal
from aredis_om import HashModel, Field
from core.redis import redis_conn as conn
from typing import TypeVar, Generic, Sequence

from db.redis.models.mapped_columns import now_moscow


T = TypeVar("T")


class ModelAdmin(HashModel, Generic[T]):

    @classmethod
    async def create(cls, ttl: int | None = None, **kwargs) -> T:
        """
            Создать новые объект в бд
        :param ttl: Время жизни нового объекта
        :return: Созданный объект
        """
        model = cls(**kwargs)
        model = await model.save()

        if ttl:
            await model.expire(ttl)

        return model

    async def update(self, **kwargs) -> None:
        """
            Обновить текущий объект в БД
        :param kwargs: Ячейки, которые вам нужно обновить
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        await self.save()

    async def delete(self) -> None:
        """
            Удалить текущий объект в БД
        """
        await super().delete(self.pk)

    @classmethod
    async def get(cls, pk: str) -> T:
        """
            Получите один объект по фильтрам
        :param pk: PK
        """
        try:
            return await super().get(pk)

        except Exception as e:
            return None

    @classmethod
    async def filter(cls, **kwargs) -> Sequence[T]:
        all_pks = await cls.all()
        result = []
        async for pk in all_pks:
            obj = await cls.get(pk)
            if obj and all(getattr(obj, k) == v for k, v in kwargs.items()):
                result.append(obj)
        return result


    async def set_ttl(self, ttl: int) -> bool:
        """
            Установите TTL для объекта
        :param ttl: TTL для объекта
        """
        return await self.expire(ttl)

    @classmethod
    async def all(cls):
        """
            Взять все ключи объектов класса
        """
        return await super().all_pks()


# Хранение сообщений с ИИ
class MessageAI(ModelAdmin):

    kwork_user_id: int = Field(index=True, description="Kwork ID пользователя")
    recipient_id: int = Field(index=True, description="ID получателя")
    sender: Literal['user', 'ai'] = Field(index=True, description="Отправитель сообщения: пользователь или ИИ")
    content: str = Field(description="Текст сообщения")
    created_at: datetime = Field(default_factory=now_moscow, index=True, description="Время создания сообщения (московское)")

    class Meta:
        database = conn

    @classmethod
    async def delete_all_for_user(cls, user_id: int):
        """
        Удалить все сообщения, где kwork_id = user_id ИЛИ recipient_id = user_id
        """
        msgs_by_kwork = await cls.filter(kwork_user_id=user_id)
        msgs_by_recipient = await cls.filter(recipient_id=user_id)

        # Объединяем списки, чтобы не удалять дважды одинаковые сообщения
        all_msgs = {msg.pk: msg for msg in msgs_by_kwork}
        for msg in msgs_by_recipient:
            all_msgs[msg.pk] = msg

        # Удаляем все уникальные сообщения
        for msg in all_msgs.values():
            await msg.delete()
