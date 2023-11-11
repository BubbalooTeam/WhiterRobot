# Copiright (C) 2023 BubbalooTeam
import asyncio
import logging

from whiterkang import WhiterX, db

GROUPS = db["GROUPS"]
USERS = db["USERS_START"]

async def find_user(uid: int):
    try:
        user = await WhiterX.get_users(uid)
        USR = await USERS.find_one({"_id": user.id})
        return bool(USR)
    except Exception as e:
        logging.error(f"An Error Ocurred: {e}")
        return False

async def add_user(uid: int):
    try:
        user = await WhiterX.get_users(uid)
        user_start = f"#NEW_USER #LOGS\n\n<b>User:</b> {user.mention}\n<b>ID:</b> {user.id} <a href='tg://user?id={user.id}'>**Link**</a>"
        if user.username:
            user_start += f"\n<b>Username:</b> @{user.username}"
        await asyncio.gather(
            DB_USER.update_one({"_id": user.id}, {"$set": {"user": user.first_name}}, upsert=True),
            WhiterX.send_log(user_start),
        )
    except Exception as e:
        logging.error(f"An Error Occurred: {e}")
        pass

async def add_gp(m):
    user = f"<a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a>"
    text_add = f"#WhiterKang #NEW_GROUP #LOGS\n\n<b>Grupo</b>: <i>{m.chat.title}</i>\n<b>ID</b>: <i>{m.chat.id}</i>\n<i>User</i>: <i>{user}</i>"
    if m.chat.username:
        text_add += f"<b>\nUsername</b>: @{m.chat.username}"
    try:
        await GROUPS.insert_one({"chat_id": m.chat.id, "title": m.chat.title}),
        await WhiterX.send_log(
            text_add, disable_notification=False, disable_web_page_preview=True
        )
    except Exception as e:
        await WhiterX.send_err(e)


async def del_gp(m):
    del_txt = f"#WhiterKang #LEFT_GROUP #LOGS\n\n<b>Group</b>: {m.chat.title}\n<b>ID</b>: {m.chat.id}"
    try:
        await GROUPS.delete_one({"chat_id": m.chat.id})
        await WhiterX.send_log(
            del_txt, disable_notification=False, disable_web_page_preview=True
        )
    except Exception as e:
        await WhiterX.send_err(e)

async def find_gp(gid):
    row = await GROUPS.find_one({"chat_id": gid})
    return bool(row)
