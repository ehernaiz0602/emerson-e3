import aiosqlite
import asyncio
import json
from datetime import datetime, timezone
import logging
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "database.db"

async def save_messages(data, ip, method):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for message in data:
            await db.execute(
            f"""
            INSERT INTO messages 
            VALUES ("{datetime.now(timezone.utc).isoformat()}", "{ip}", '{json.dumps(message)}', "{method}", 0)
            """
            )
        await db.commit()

async def clear_messages(processed_only: bool = False):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if processed_only:
            await db.execute(f"""DELETE FROM messages WHERE processed = 1""")
            logging.debug(f"Clearing local database of all processed messages")
        else:
            await db.execute(f"""DELETE FROM messages""")
            logging.info(f"Clearing local database of all messages")
        await db.commit()

        await db.execute(f"""VACUUM""")
        await db.commit()

async def remove_bottom_n_records(n: int, max_n: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(f"SELECT COUNT(*) FROM messages") as cursor:
            count = await cursor.fetchone()
        logging.debug(f"Count of offline messages: {count[0]}")
        if count[0] > max_n:
            logging.info(f"Offline messages ({count[0]}) exceeded maximum of {max_n}, trimming {n} messages")
            async with db.execute(f"""
                DELETE FROM messages
                WHERE rowid IN (
                    SELECT rowid FROM messages
                    ORDER BY timestamp DESC
                    LIMIT -1 OFFSET (SELECT COUNT(*) FROM messages) - {n}
                )
            """) as _:
                await db.commit()

            async with db.execute(f"""VACUUM""") as _:
                await db.commit()
            logging.debug(f"Trimmed {n} offline messages")
        else:
            logging.debug(f"Offline messages count under max limit, skipping trim")

async def load_and_set_rows():
    async with aiosqlite.connect(DATABASE_PATH) as db:

        logging.debug("Loading queued messages into memory")
        async with db.execute(f"SELECT * FROM messages WHERE processed = 0") as cursor:
            rows = await cursor.fetchall()
            
        await db.execute(f"UPDATE messages SET processed = 1")
        
        await db.commit()
        return rows

async def unset_rows():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        logging.debug("Unsetting the processed rows")
        async with db.execute("UPDATE messages SET processed = 0") as _:
            await db.commit()
        logging.debug("Unset the processed messages")

