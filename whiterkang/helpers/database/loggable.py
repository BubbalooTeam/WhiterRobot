from whiterkang import WhiterX, db

DB_LOGS = db["CHAT_LOGS"]

async def add_chat_log(chat_id: int, log_id: int):
    await DB_LOGS.update_one({"chat_id": chat_id}, {"$set": {"log_chat": log_id}}, upsert=True)
    return

async def del_chat_log(chat_id: int):
    await DB_LOGS.delete_many({"chat_id": chat_id})
    return

async def get_chat_log(chat_id: int):
    finders = await DB_LOGS.find_one({"chat_id": chat_id})
    if finders:
        res = finders["log_chat"]
        return [True, res]
    else:
        return [False, None]
    
async def send_chat_log(chat_id: int, text: str, fun: str):
    res = await get_chat_log(chat_id)
    if res[0] == True:
        base = "#{}".format(fun.upper())
        txt = base + "\n" + text
        try:
            await WhiterX.send_message(res[1], txt)
        except Exception as e:
            try:
                await WhiterX.send_message(chat_id, "<i>Unsetting LogChat...</i>\n<b>Reason:</b> <code>{}</code>".format(e))
                await del_chat_log(chat_id)
            except Exception:
                await del_chat_log(chat_id)
                return
        return
    else:
        return