import html
import asyncio

from hydrogram.types import Message

from typing import Optional

from whiterkang import WhiterX, Config, db
from whiterkang.helpers import is_dev, sw, tld, check_bot_rights, is_self

antispam_db = db["ANTISPAM_CHATS"]
gban_db = db["GBAN"]

LOGS = Config.GBAN_LOGS

async def gban_user(m: Message, user_id: int, user_name: str, admin_name: str, reason: Optional[str] = None):
    if is_dev(user_id):
        await m.reply(await tld(m.chat.id, "ANTISPAM_ERR_USR_SUDO"))
        await gban_db.delete_many({"user_id": user_id})
        return
    elif await is_self(user_id):
        await m.reply(await tld(m.chat.id, "ANTISPAM_ERR_USR_BOT"))
    else:
        gban_results = await gban_db.find_one({"user_id": user_id})
        if not gban_results:
            if reason == None:
                await m.reply(await tld(m.chat.id, "ANTISPAM_NO_REASON"))
                return
            
            await gban_db.insert_one({"user_id": user_id, "reason": reason})

            find_chats = antispam_db.find({"status": True})

            count = 0
            async for chats in find_chats:
                chat_id = chats["chat_id"]
                # Try ban user gbanned
                try:
                    if not await check_bot_rights(chat_id, "can_restrict_members"):
                        pass
                
                    await WhiterX.ban_chat_member(chat_id, user_id)
                    count += 1
                except Exception:
                    continue
            await m.reply((await tld(m.chat.id, "ANTISPAM_NEW_GBAN")).format(user_name, user_id, reason))
            if not LOGS == "None":
                group_logs = LOGS
                try:
                    id_log = int(group_logs)
                    await WhiterX.send_message(id_log, (await tld(id_log, "ANTISPAM_LOGGER_NEW_GBAN")).format(admin_name, user_name, user_id, reason, count))
                    return
                except Exception as e:
                    await asyncio.gather(WhiterX.send_err(e))
                    return
        else:
            if reason == None:
                await m.reply(await tld(m.chat.id, "ANTISPAM_ERR_NO_NEW_REASON"))
                return
            else:
                try:
                    old_find = await gban_db.find_one({"user_id": user_id})
                    old_reason = old_find["reason"]
                    await gban_db.update_one({"user_id" : user_id}, {"$set": {"reason": reason}}, upsert=True)
                except Exception as e:
                    await m.reply(e)
                    return

                find_chats = antispam_db.find()

                async for chats in find_chats:
                    chat_id = chats["chat_id"]
                    # Try ban user gbanned
                    try:
                        if not await check_bot_rights(chat_id, "can_restrict_members"):
                            pass
                
                        await WhiterX.ban_chat_member(chat_id, user_id)
                    except Exception:
                        continue
                await m.reply((await tld(m.chat.id, "ANTISPAM_REASON_UPDATED")).format(old_reason, reason))
                if not LOGS == "None":
                    group_logs = LOGS
                    try:
                        id_log = int(group_logs)
                        await WhiterX.send_message(id_log, (await tld(id_log, "ANTISPAM_LOGGER_UPDATE_GBAN")).format(admin_name, user_name, user_id, old_reason, reason))
                        return
                    except Exception as e:
                        err = f"{e} Line {e.__traceback__.tb_lineno}"
                        await asyncio.gather(WhiterX.send_err(err))
                        return

async def check_ban(m: Message, chat_id: int, user_id: int):
    try:
        if is_dev(user_id):
            pass
        elif sw != None:
            sw_response = sw.get_ban(user_id)
            if sw_response:
                sw_reason = sw_response.reason
                if await check_bot_rights(chat_id, "can_restrict_members"):
                    await WhiterX.ban_chat_member(chat_id, user_id)
                    await m.reply((await tld(chat_id, "ANTISPAM_SPAMWATCH_BANNED")).format(sw_reason))
                    return await m.stop_propagation()
                else:
                    pass
            else:
                gbanned = await gban_db.find_one({"user_id": user_id})
                if gbanned:
                    usrreason = gbanned["reason"]
                    if usrreason:
                        if await check_bot_rights(chat_id, "can_restrict_members"):
                            await WhiterX.ban_chat_member(chat_id, user_id)
                            await m.reply((await tld(chat_id, "ANTISPAM_CHECKBAN_USER_REMOVED")).format(usrreason))
                            return await m.stop_propagation()
                        else:
                            pass
                    else:
                        pass
    except Exception:
        pass

async def ungban_user(m: Message, user_id: int, user_name: str, admin_name: str, reason: str):
    gban_results = await gban_db.find_one({"user_id": user_id})
    if not gban_results:
        await m.reply(await tld(m.chat.id, "ANTISPAM_USER_NOT_GBANNED"))
        return
    else:
        if gban_results:
            if reason == None:
                await m.reply(await tld(m.chat.id, "ANTISPAM_NO_REASON"))
                return
            
            await gban_db.delete_many({"user_id": user_id})

            find_chats = antispam_db.find({"status": True})

            count = 0
            
            async for chats in find_chats:
                chat_id = chats["chat_id"]
                # Try unban user gbanned
                try:
                    if not await check_bot_rights(chat_id, "can_restrict_members"):
                        pass
                
                    await WhiterX.unban_chat_member(chat_id, user_id)
                    count += 1
                except Exception:
                    continue
            await m.reply(await tld(m.chat.id, "ANTISPAM_UNGBANNED"))
            if not LOGS == "None":
                group_logs = LOGS
                try:
                    id_log = int(group_logs)
                    await WhiterX.send_message(id_log, (await tld(id_log, "ANTISPAM_LOGGER_UNGBAN")).format(admin_name, user_name, user_id, reason, count))
                    return
                except Exception as e:
                    await asyncio.gather(WhiterX.send_err(e))
                    await m.reply((await tld(m.chat.id, "ANTISPAM_ERR_UNGBAN")).format(e))
                    return
                    

async def check_antispam(chat_id: int):
    atspam = await antispam_db.find_one({"chat_id": chat_id, "status": True})
    if atspam:
        return True
    else:
        return False
