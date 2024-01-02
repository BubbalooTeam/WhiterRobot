import uuid

from whiterkang import WhiterX, db

from contextlib import suppress
from typing import Optional

from hydrogram.errors import ChatIdInvalid, ChatWriteForbidden, ChatInvalid

DB_FEDS = db["FEDS"]

async def fed_post_log(fed, text):
    if "log_chat_id" not in fed:
        return
    chat_id = fed["log_chat_id"]
    with suppress(ChatWriteForbidden, ChatIdInvalid, ChatInvalid):
        await WhiterX.send_message(chat_id, text)

async def get_fed_by_id(fed_id: str) -> Optional[dict]:
    return await DB_FEDS.find_one({'fed_id': fed_id})

async def get_fed_by_creator(creator: int) -> Optional[dict]:
    return await DB_FEDS.find_one({'creator': creator})

async def get_fed_by_name(fed_name: str):
    return await DB_FEDS.find_one({'fed_name': fed_name})

async def add_fed(fed_name, creator_id):
    fed_id = str(uuid.uuid4())
    data = {
        "fed_name": fed_name,
        "fed_id": fed_id
    }
    await DB_FEDS.update_one({"creator": creator_id}, {"$set": data}, upsert=True)
    return creator_id, fed_name, fed_id

async def add_fed_chat(fed_id, chat_id):
    await DB_FEDS.update_one(
        {'_id': fed_id},
        {"$set": {'chats': {'$each': [chat_id]}}}, upsert=True
    )
async def del_fed_chat(fed_id, chat_id):
    await DB_FEDS.update_one(
        {'_id': fed_id},
        {"$pull": {'chats': {'$each': [chat_id]}}}, upsert=True
    )
