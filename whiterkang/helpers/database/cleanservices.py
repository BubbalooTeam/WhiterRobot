import logging
from whiterkang import db

DB_CLEANSERVICE = db["CLEANSERVICE"]

async def clean_service_add(chat_id: int):
    try:
        await DB_CLEANSERVICE.update_one({"chat_id": chat_id}, {"$set": {"status": "on"}}, upsert=True)
    except Exception as e:
        logging.error("An error occurred: {}".format(e))

async def clean_service_find(chat_id: int):
    try:
        await DB_CLEANSERVICE.find_one({"chat_id": chat_id, "status": "on"})
    except Exception as e:
        logging.error("An error occurred: {}".format(e))

async def clean_service_del(chat_id: int):
    try:
        await DB_CLEANSERVICE.delete_many({"chat_id": chat_id})
    except Exception as e:
        logging.error("An error occurred: {}".format(e))