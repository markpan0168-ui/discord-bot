import aiosqlite

async def add_mod_stat(mod_id, column):
    async with aiosqlite.connect("mod.db") as db:
        await db.execute(f"""
        INSERT INTO modstats (moderator_id, {column})
        VALUES (?, 1)
        ON CONFLICT(moderator_id)
        DO UPDATE SET {column} = {column} + 1
        """, (mod_id,))
        await db.commit()


async def add_stat(user_id, column):
    async with aiosqlite.connect("mod.db") as db:
        await db.execute(f"""
        INSERT INTO stats (user_id, {column})
        VALUES (?, 1)
        ON CONFLICT(user_id)
        DO UPDATE SET {column} = {column} + 1
        """, (user_id,))
        await db.commit()
