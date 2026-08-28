import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL UNIQUE COLLATE NOCASE,
                chat_id INTEGER NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_owner_chat_id(nickname: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT chat_id FROM links WHERE nickname = ?", (nickname,)
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def link_account(nickname: str, chat_id: int, password_hash: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO links (nickname, chat_id, password_hash) VALUES (?, ?, ?)",
            (nickname, chat_id, password_hash),
        )
        await db.commit()


async def get_links_for_chat(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT nickname, created_at FROM links WHERE chat_id = ? ORDER BY created_at",
            (chat_id,),
        )
        return await cur.fetchall()


async def update_password(nickname: str, new_hash: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE links SET password_hash = ? WHERE nickname = ?",
            (new_hash, nickname),
        )
        await db.commit()
