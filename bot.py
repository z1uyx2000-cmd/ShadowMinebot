import asyncio
import hashlib
import logging
import os
import secrets

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiohttp import web

from config import BOT_TOKEN
import database as db

logging.basicConfig(level=logging.INFO)

router = Router()


def hash_password(raw: str) -> str:
    # Простой SHA-256. В Java-плагине пароль нужно хэшировать так же:
    # MessageDigest.getInstance("SHA-256")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


HELP_TEXT = (
    "[Бот] Список команд привязки:\n"
    "- /tg НИК ПАРОЛЬ — Привязать аккаунт к текущей странице\n"
    "  *Внимание! Можно привязать несколько аккаунтов.\n"
    "- /list — Список привязанных аккаунтов\n"
    "- /recovery НИК — Сбросить пароль от аккаунта"
)

START_TEXT = (
    "[Бот] Для того, чтобы привязать игровой аккаунт к Вашей странице ТГ, "
    "выполните следующие действия:\n"
    "1. Напишите (сюда): /tg Ваш-Ник Ваш-Пароль\n"
    "2. Напишите /help (сюда), чтобы увидеть возможности.\n"
    "Приятной игры на наших серверах!"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(START_TEXT)


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT)


@router.message(Command("tg"))
async def cmd_tg(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) != 3:
        await message.answer(
            "[Бот] Неверный формат. Используйте: /tg НИК ПАРОЛЬ"
        )
        return

    _, nickname, password = args

    if len(password) < 4:
        await message.answer("[Бот] Пароль слишком короткий (минимум 4 символа).")
        return

    owner = await db.get_owner_chat_id(nickname)
    if owner is not None:
        await message.answer(
            f"[Бот] Ник {nickname} уже привязан к чьей-то странице. "
            f"Если это Вы — используйте /recovery {nickname}"
        )
        return

    await db.link_account(nickname, message.chat.id, hash_password(password))
    await message.answer(
        f"[Бот] Аккаунт {nickname} успешно привязан к Вашей странице!\n"
        f"Теперь заходите в игру и указывайте этот пароль при входе."
    )


@router.message(Command("list"))
async def cmd_list(message: Message):
    links = await db.get_links_for_chat(message.chat.id)
    if not links:
        await message.answer("[Бот] У Вас пока нет привязанных аккаунтов.")
        return

    text = "[Бот] Привязанные аккаунты:\n" + "\n".join(
        f"- {nick} (привязан {created})" for nick, created in links
    )
    await message.answer(text)


@router.message(Command("recovery"))
async def cmd_recovery(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        await message.answer("[Бот] Используйте: /recovery НИК")
        return

    nickname = args[1].strip()
    owner = await db.get_owner_chat_id(nickname)

    if owner is None:
        await message.answer(f"[Бот] Ник {nickname} не найден среди привязанных.")
        return

    if owner != message.chat.id:
        await message.answer(
            f"[Бот] Аккаунт {nickname} привязан не к Вашей странице."
        )
        return

    new_password = secrets.token_urlsafe(6)
    await db.update_password(nickname, hash_password(new_password))
    await message.answer(
        f"[Бот] Пароль для {nickname} сброшен.\n"
        f"Новый пароль: {new_password}\n"
        f"Используйте его при следующем входе в игру."
    )


async def health(request):
    return web.Response(text="Bot is alive")


async def start_web_server():
    # Render требует, чтобы сервис слушал порт из переменной PORT
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    await db.init_db()
    await start_web_server()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
