from pathlib import Path
from typing import Optional, Tuple

from openai import AsyncOpenAI
from db.models.models import Message
from settings import settings


class GPTHandler:

    def __init__(self, kwork_user_id: int, recipient_id: int):
        self.kwork_user_id = kwork_user_id
        self.recipient_id = recipient_id
        self.prompt_path = Path("data/prompt.txt")
        self.client = AsyncOpenAI(api_key=settings.openai.TOKEN)

    async def load_prompt(self) -> str:
        if self.prompt_path.exists():
            return self.prompt_path.read_text(encoding='utf-8')
        return ""

    async def get_history(self) -> list[dict]:
        """
        Возвращает историю сообщений между пользователем и ИИ, только текст.
        Включает как сообщения пользователя, так и ответы ИИ.
        """

        # Сообщения пользователя
        user_messages = await Message.filter(
            kwork_user_id=self.kwork_user_id,
            recipient_id=self.recipient_id,
            tg_msg_id=None
        )

        # Ответы ИИ
        assistant_messages = await Message.filter(
            recipient_id=self.kwork_user_id,
            kwork_user_id=1,
            tg_msg_id=None
        )

        history = []

        for msg in user_messages:
            if msg.text:
                history.append({
                    "role": "user",
                    "content": msg.text
                })

        for msg in assistant_messages:
            if msg.text:
                history.append({
                    "role": "assistant",
                    "content": msg.text
                })

        # Сортировка по времени, если в модели есть created_at
        history.sort(key=lambda x: x.get("created_at", 0))
        return history

    async def generate_response(self) -> Tuple[str, Optional[str]]:
        """
        Возвращает ответ GPT и, если есть, заявку вида 🚨 Новый заказ ... (в отдельной переменной).
        """
        history = await self.get_history()
        prompt = await self.load_prompt()

        full_messages = [{"role": "system", "content": prompt}] + history

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=full_messages,
        )

        reply = response.choices[0].message.content.strip()

        application_text = None
        if "🚨 Новый заказ" in reply:
            lines = reply.splitlines()
            start = None
            end = None

            for i, line in enumerate(lines):
                if "🚨 Новый заказ" in line:
                    start = i
                elif start is not None and line.strip() == "":
                    end = i
                    break

            # Если нашли блок заявки
            if start is not None:
                end = end if end is not None else len(lines)
                application_text = "\n".join(lines[start:end]).strip()

                # Убираем заявку из ответа
                reply = "\n".join(lines[:start] + lines[end:]).strip()

                if not reply.strip() and application_text:
                    reply = "Спасибо! Мы приняли заявку. Ожидайте, пожалуйста, обратной связи."

        return reply.replace('`', ''), application_text