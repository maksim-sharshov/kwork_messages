from datetime import timedelta
from typing import TypeVar, Generic, Sequence

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Mapped, selectinload, load_only
from sqlalchemy.sql import select, update as sqlalchemy_update
from sqlalchemy import ForeignKey, Boolean,  select, not_, func

from core.database import async_db_session, Base
from db.psql.models.enum import *
from db.psql.models.mapped_columns import *
from db.psql.models.mapped_columns import now_moscow


T = TypeVar("T")


class ModelAdmin(Generic[T]):
    
    class DoesNotExists(Exception):
        pass

    @classmethod
    async def create(cls, **kwargs) -> T:
        """
        # Создает новый объект и возвращает его.
        :param kwargs: Поля и значения для объекта.
        :return: Созданный объект.
        """

        async with async_db_session() as session:
            obj = cls(**kwargs)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    @classmethod
    async def add(cls, **kwargs) -> None:
        """
        # Создает новый объект.
        :param kwargs: Поля и значения для объекта.
        """

        async with async_db_session() as session:
            session.add(cls(**kwargs))
            await session.commit()

    async def update(self, **kwargs) -> None:
        """
        # Обновляет текущий объект.
        :param kwargs: Поля и значения, которые надо поменять.
        """

        async with async_db_session() as session:
            await session.execute(
                sqlalchemy_update(self.__class__), [{"id": self.id, **kwargs}]
            )
            await session.commit()

    async def delete(self) -> None:
        """
        # Удаляет объект.
        """
        async with async_db_session() as session:
            await session.delete(self)
            await session.commit()

    @classmethod
    async def get(cls, select_in_load: str | None = None, **kwargs) -> T | None:
        """
        # Возвращает одну запись, которая удовлетворяет введенным параметрам.

        :param select_in_load: Загрузить сразу связанную модель.
        :param kwargs: Поля и значения.
        :return: Объект или None если не найдено.
        """

        params = [getattr(cls, key) == val for key, val in kwargs.items()]
        query = select(cls).where(*params)

        if select_in_load:
            query.options(selectinload(getattr(cls, select_in_load)))

        try:
            async with async_db_session() as session:
                results = await session.execute(query)
                (result,) = results.one()
                return result
        except NoResultFound:
            return None

    @classmethod
    async def filter(cls, select_in_load: str | None = None, **kwargs) -> Sequence[T]:
        """
        # Возвращает все записи, которые удовлетворяют фильтру.

        :param select_in_load: Загрузить сразу связанную модель.
        :param kwargs: Поля и значения.
        :return: Перечень записей.
        """

        params = [getattr(cls, key) == val for key, val in kwargs.items()]
        query = select(cls).where(*params)

        if select_in_load:
            query.options(selectinload(getattr(cls, select_in_load)))

        try:
            async with async_db_session() as session:
                results = await session.execute(query)
                return results.scalars().all()
        except NoResultFound:
            return ()

    @classmethod
    async def all(
            cls, select_in_load: str = None, values: list[str] = None
    ) -> Sequence[T]:
        """
        # Получает все записи.

        :param select_in_load: Загрузить сразу связанную модель.
        :param values: Список полей, которые надо вернуть, если нет, то все (default None).
        """

        if values and isinstance(values, list):
            # Определенные поля
            values = [getattr(cls, val) for val in values if isinstance(val, str)]
            query = select(cls).options(load_only(*values))
        else:
            # Все поля
            query = select(cls)

        if select_in_load:
            query.options(selectinload(getattr(cls, select_in_load)))

        async with async_db_session() as session:
            result = await session.execute(query)
            return result.scalars().all()


class User(Base, ModelAdmin):
    
    __tablename__ = 'users'

    id: Mapped[intpk]
    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True
    )
    username: Mapped[str_32 | None] = mapped_column(
        unique=True,
        comment='Username пользователя'
    )
    role: Mapped[Role | None] = mapped_column(
        default=Role.USER,
        comment='Роль пользователя'
    )
    created_at: Mapped[created_at]


class Chat(Base, ModelAdmin):

    __tablename__ = 'chats'

    id: Mapped[intpk]
    kwork_user_id: Mapped[int] = mapped_column(
        BigInteger,
        comment='ID чата в Kwork'
    )
    tg_chat_id: Mapped[int] = mapped_column(
        BigInteger,
        comment='ID чата в тг'
    )
    tg_topic_id: Mapped[int] = mapped_column(
        BigInteger,
        comment='ID топика в группе'
    )
    title: Mapped[str] = mapped_column(comment='Имя топика')
    account_id = mapped_column(ForeignKey('accounts.id'))


class Account(Base, ModelAdmin):

    __tablename__ = 'accounts'

    id: Mapped[intpk]
    cookie: Mapped[str] = mapped_column(comment='Куки для доступа к аккаунту')
    username: Mapped[str | None] = mapped_column(comment='Username аккаунта')
    created_at: Mapped[created_at | None]


class Message(Base, ModelAdmin):

    __tablename__ = 'messages'

    id: Mapped[intpk]
    kwork_user_id: Mapped[int] = mapped_column(
        BigInteger,
        comment='От кого сообщение'
    )
    username: Mapped[str_240] = mapped_column(
        comment='От кого сообщение'
    )
    kwork_msg_id: Mapped[int] = mapped_column(
        BigInteger,
        comment='ID сообщения в kwork'
    )
    recipient_kwork_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        comment='ID получателя в Kwork'
    )
    tg_msg_id: Mapped[int] = mapped_column(
        BigInteger,
        comment='ID сообщения в тг чате'
    )
    viewed: Mapped[bool | None] = mapped_column(
        comment='Сообщение просмотрено',
        default=False
    )
    text: Mapped[str] = mapped_column(comment='Текст сообщения')

    created_at: Mapped[created_at]

    @classmethod
    async def get_users_for_reminder(cls) -> list[int]:
        """
        Возвращает список kwork_user_id пользователей, которым нужно отправить напоминание
        "Подскажите пожалуйста, ваш проект ещё актуален?".

        Условия:
        - Последнее сообщение в диалоге (от пользователя или бота) старше 2 часов.
        - Знаем, кому было отправлено последнее сообщение (recipient_kwork_user_id != 0).
        - Бот ещё не отправлял этому пользователю напоминание за последние 2 часа.

        Используется для напоминания неактивным пользователям, независимо от того, кто писал последний.
        """
        reminder_text = "Подскажите пожалуйста, ваш проект ещё актуален?"
        now = now_moscow()
        two_hours_ago = now - timedelta(hours=2)

        async with async_db_session() as session:

            # 1) Кому уже отправляли напоминание за последние 2 часа
            subq_bot_sent = (
                select(cls.recipient_kwork_user_id)
                .where(
                    cls.kwork_user_id == 0,
                    cls.text == reminder_text,
                    cls.recipient_kwork_user_id != 0,
                    cls.created_at >= two_hours_ago
                )
                .distinct()
                .subquery()
            )

            # 2) Последнее сообщение в диалоге (не важно от кого)
            last_messages = (
                select(
                    cls.recipient_kwork_user_id.label("user_id"),
                    func.max(cls.created_at).label("last_msg_time")
                )
                .where(
                    cls.recipient_kwork_user_id != 0
                )
                .group_by(cls.recipient_kwork_user_id)
                .subquery()
            )

            # 3) Берём только тех, с кем не было общения 2+ часа и кому бот не писал напоминание
            query = (
                select(last_messages.c.user_id)
                .where(
                    last_messages.c.last_msg_time <= two_hours_ago,
                    not_(last_messages.c.user_id.in_(select(subq_bot_sent.c.recipient_kwork_user_id)))
                )
            )

            result = await session.execute(query)
            users = result.scalars().all()

            return users


class ManagerMode(Base, ModelAdmin):

    __tablename__ = 'manager_mode'

    id: Mapped[intpk]
    kwork_user_id: Mapped[int] = mapped_column(
        BigInteger,
        comment='От кого сообщение'
    )
    flag: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment='False — отвечает ИИ, True — отвечает менеджер'
    )