from whiterkang import db

DISABLED = db["DISABLED"]

async def is_disabled(gid: int, query: str) -> bool:
    off = await DISABLED.find_one({"chat_id": gid, "cmd": query})
    return bool(off)
