import datetime
from whiterkang import WhiterX, db
from .tools import extract_time

ANTIFLOOD = db["ANTIFLOOD"]
MSG_CACHE = {}

class AntiFloodChat:
    async def flood_time(self, chat_id: int):
        finders = await ANTIFLOOD.find_one({"chat_id": chat_id})
        if finders:
            res = finders["timest"]
        else:
            res = "10s"
        return res
    
    async def compare_time(self, chat_id: int):
        finders = await self.flood_time(chat_id)

        extime = extract_time(finders)
        extmr = datetime.datetime.now() - extime
        fnlly = extmr.total_seconds
        if fnlly >= finders:
            return True
        else:
            return False

    async def flood_limit(self, chat_id: int):
        finders = await ANTIFLOOD.find_one({"chat_id": chat_id})
        if finders:
            res = finders["flimit"]
        else:
            res = 5
        return res

    async def cache_flood(self, chat_id: int, user_id: int):
        if not MSG_CACHE[chat_id][user_id]:
            MSG_CACHE[chat_id][user_id] = {
                "count": 1,
                "time": datetime.datetime.now(),
            }
            return False
        
        chat_flood = MSG_CACHE[chat_id][user_id]

        if await self.compare_time(chat_id):
            del chat_flood
            return False

        count = int(chat_flood["count"]) + 1

        if count >= await self.flood_limit(chat_id):
            del chat_flood
            return True
        
        chat_flood = {
            "count": count, 
            "time": datetime.datetime.now()
        }
        return False
    
    async def antiflood_toggle(self, chat_id: int, toggle: bool):
        return await ANTIFLOOD.update_one({"chat_id": chat_id}, {"$set": {"toggled": toggle}})
        
    async def antiflood_settime(self, chat_id: int, time: str):
        return await ANTIFLOOD.update_one({"chat_id": chat_id}, {"$set": {"timest": time}})
    
    async def antiflood_setlimit(self, chat_id: int, limit: int):
        return await ANTIFLOOD.update_one({"chat_id": chat_id}, {"$set": {"flimit": limit}})
    
antifloodchat = AntiFloodChat()