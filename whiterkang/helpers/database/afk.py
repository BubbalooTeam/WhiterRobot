import humanize

from datetime import datetime

from whiterkang import db
from whiterkang.helpers import tld

AFK = db["_AFK"]

async def add_afk_reason(user_id: int, reason: str, time: str):
    await AFK.update_one({"user_id": user_id}, {"$set": {"_afk": "on", "_reason": reason, "time": time}}, upsert=True)

async def add_afk(user_id: int, time: str):
    await AFK.update_one({"user_id": user_id}, {"$set": {"_afk": "on", "time": time}}, upsert=True)

async def del_afk(user_id: int):
    await AFK.delete_many({"user_id": user_id})

async def is_afk(user_id: int):
    res = await AFK.find_one({"user_id": user_id, "_afk": "on"})
    return bool(res)

async def find_reason_afk(user_id: int):
    res = await AFK.find_one({"user_id": user_id, "_afk": "on"})
    if "_reason" in res:
        resp = res["_reason"]
        return resp
    else:
        return None

async def check_afk(m, user_id, user_fn, user):
    if user_id == user.id:
        return
    #AFK data
    afk_found = await AFK.find_one({"user_id": user_id, "_afk": "on"})
    #Ifs from get data
    if afk_found:
        try:
            await m.chat.get_member(int(user_id))  # Check if the user is in the group
        except (UserNotParticipant, PeerIdInvalid):
            return

        #time afk:
        if (lang := await tld(m.chat.id, "language")) != "en":
            humanize.i18n.activate(lang)
        time = humanize.naturaldelta(datetime.now() - datetime.fromtimestamp(afk_found["time"]))
        
        if "_reason" in afk_found:
            r = afk_found["_reason"]
            afkmsg = (await tld(m.chat.id, "IS_AFK_REASON")).format(user_fn, r, time)
        else:
            afkmsg = (await tld(m.chat.id, "IS_AFK")).format(user_fn, time)
        try:
            return await m.reply_text(afkmsg)
        except ChatWriteForbidden:
            return
