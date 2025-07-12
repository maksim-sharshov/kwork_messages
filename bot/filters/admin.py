from aiogram.filters import Filter
from aiogram.types import Message

from db.psql.models.enum import Role
from db.psql.models.models import User


class IsManager(Filter):
    async def __call__(self, message: Message) -> bool:
        user = await User.get(tg_id=message.from_user.id)
        return user.role == Role.MANAGER or user.role == Role.ADMIN
