from whiterkang import db

from typing import Optional

CSDL = db["MEDIAS"]
CISDL = db["CAPTION_SDL"]

async def csdl(ugid: int) -> bool:
    row = await CSDL.find_one({"chat_id": ugid, "status": True})
    return bool(row)

async def tsdl(ugid: int, mode: Optional[bool]) -> None:
    await CSDL.update_one({"chat_id": ugid}, {"$set": {"status": mode}}, upsert=True)  
    
async def cisdl(ugid: int) -> bool:
    row = await CISDL.find_one({"chat_id": ugid, "status": True})
    return bool(row)

async def tisdl(ugid: int, mode: Optional[bool]) -> None:
    await CISDL.update_one({"chat_id": ugid}, {"$set": {"status": mode}}, upsert=True)
    
