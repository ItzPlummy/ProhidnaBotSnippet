import asyncio
from json import loads, dumps
from types import NoneType
from typing import List, Dict, Any, Type

from aiogram import Bot
from aiogram.exceptions import AiogramError
from redis.asyncio import Redis


class TempMessageManager:
    def __init__(
            self,
            bot: Bot,
            redis: Redis | None = None,
    ) -> None:
        self.bot = bot
        self.redis = redis
        self.temp_messages: Dict[int, List[int]] = {}

        self.manager_strategy_dict: Dict[Type[Redis] | NoneType, dict[str, Any]] = {
            Redis: {
                "add": self.__add_to_redis,
                "clear": self.__clear_from_redis
            },
            NoneType: {
                "add": self.__add_to_memory,
                "clear": self.__clear_from_memory
            }
        }

    async def clear(
            self,
            chat_id: int
    ) -> None:
        await asyncio.create_task(self.manager_strategy_dict[type(self.redis)]["clear"](chat_id))

    async def add(
            self,
            chat_id: int,
            message_id: int
    ) -> None:
        await asyncio.create_task(self.manager_strategy_dict[type(self.redis)]["add"](chat_id, message_id))

    async def __add_to_memory(
            self,
            chat_id: int,
            message_id: int
    ) -> None:
        if chat_id not in self.temp_messages:
            self.temp_messages.update({chat_id: []})

        self.temp_messages.get(chat_id).append(message_id)

    async def __clear_from_memory(
            self,
            chat_id: int
    ) -> None:
        if chat_id not in self.temp_messages:
            return

        for message_id in self.temp_messages.get(chat_id):
            try:
                await self.bot.delete_message(chat_id, message_id)
                await asyncio.sleep(0.1)
            except AiogramError:
                continue

        self.temp_messages.get(chat_id).clear()

    async def __add_to_redis(
            self,
            chat_id: int,
            message_id: int
    ) -> None:
        value: str | bytes | None = await self.redis.get(f"temp:{chat_id}")

        try:
            if value is None:
                messages: List[str] = []
            else:
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                messages: List[str] = loads(str(value))

            messages.append(str(message_id))
            await self.redis.set(f"temp:{chat_id}", dumps(messages))
        except UnicodeDecodeError:
            pass

    async def __clear_from_redis(
            self,
            chat_id: int
    ) -> None:
        value: str | bytes | None = await self.redis.get(f"temp:{chat_id}")

        try:
            if value is None:
                return

            if isinstance(value, bytes):
                value = value.decode("utf-8")

            messages: List[str] = loads(str(value))

            for message_id in messages:
                try:
                    await self.bot.delete_message(chat_id, int(message_id))
                    await asyncio.sleep(0.1)
                except AiogramError:
                    continue
        except UnicodeDecodeError:
            pass

        await self.redis.delete(f"temp:{chat_id}")
