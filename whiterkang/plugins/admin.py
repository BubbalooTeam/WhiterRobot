import uuid
import asyncio
import re
import math
import inspect
import os.path


from hydrogram import filters
from hydrogram.errors import PeerIdInvalid, UserIdInvalid, UsernameInvalid, BadRequest
from hydrogram.errors.exceptions.bad_request_400 import ChatNotModified
from hydrogram.types import ChatPermissions, Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from hydrogram.enums import ChatMemberStatus, ChatMembersFilter, ChatType

from datetime import datetime, timedelta
from functools import partial, wraps
from string import Formatter
from typing import Callable, List, Optional, Union


from whiterkang import WhiterX, Config, db
from whiterkang.helpers import (
    tld, 
    is_admin,
    check_bot_rights,
    check_rights,
    is_dev,
    is_self,
    unwarn_bnt,
    disableable_dec,
    is_disabled,
    check_antispam,
    check_ban,
    add_user,
    find_user,
    add_gp,
    input_str,
    DISABLABLE_CMDS,
    group_locks,
    group_filter,
)
from whiterkang.helpers.tools import extract_time

#warns
WARN_ACTION = db["WARN_ACTION"]
DB_WARNS = db["WARNS"]
WARNS_LIMIT = db["WARN_LIMIT"]

#rules
RULES_DB = db["RULES"]

#Greetings
GOODBYES_DB = db["GOODBYE_CHAT"]
GOODBYES_STATUS = db["GOODBYE_STATUS"]

DB_WELCOME = db["WELCOME_CHAT"]
WELCOME_STATUS = db["WELCOME_STATUS"]
CAPTCHA_DB = db["CAPTCHA"]

# Notes and Filters
DB_NOTES = db["CHAT_NOTES"]
DB_FILTERS = db["CHAT_FILTERS"]

# Disable/enable
DB_DISABLEABLE = db["DISABLED"]


SMART_OPEN = "“"
SMART_CLOSE = "”"
START_CHAR = ("'", '"', SMART_OPEN)

RESTRICTED_SYMBOLS_IN_NOTENAMES = [
    ':', '**', '__', '`', '#', '"', '[', ']', "'", '$', '||']


BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)\]\(buttonurl:(?:/{0,2})(.+?)(:same)?\))")

LOCK_TYPES = {
    "messages": "can_send_messages",
    "stickers": "can_send_other_messages",
    "gifs": "can_send_other_messages",
    "media": "can_send_media_messages",
    "games": "can_send_other_messages",
    "inline": "can_send_other_messages",
    "polls": "can_send_polls",
    "group_info": "can_change_info",
    "useradd": "can_invite_users",
    "pin": "can_pin_messages",
}

async def current_chat_permissions(chat_id):
    perms = []
    perm = (await WhiterX.get_chat(chat_id)).permissions
    if perm.can_send_messages:
        perms.append("can_send_messages")
    if perm.can_send_media_messages:
        perms.append("can_send_media_messages")
    if perm.can_send_other_messages:
        perms.append("can_send_other_messages")
    if perm.can_send_polls:
        perms.append("can_send_polls")
    if perm.can_change_info:
        perms.append("can_change_info")
    if perm.can_invite_users:
        perms.append("can_invite_users")
    if perm.can_pin_messages:
        perms.append("can_pin_messages")

    return perms

async def tg_lock(m, permissions: list, perm: str, lock: bool):
    if lock:
        if perm not in permissions:
            return await m.reply_text("Already locked.")
        permissions.remove(perm)
    else:
        if perm in permissions:
            return await m.reply_text("Already Unlocked.")
        permissions.append(perm)

    permissions = {perm: True for perm in list(set(permissions))}

    try:
        await WhiterX.set_chat_permissions(
            m.chat.id, ChatPermissions(**permissions)
        )
    except ChatNotModified:
        return await m.reply_text(
            "To unlock this, you have to unlock 'messages' first."
        )

    await m.reply_text(("Locked." if lock else "Unlocked."))

def get_urls_from_text(text: str) -> bool:
    regex = r"""(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]
                [.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(
                \([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\
                ()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))""".strip()
    return [x[0] for x in re.findall(regex, str(text))]


def get_format_keys(string: str) -> List[str]:
    """Return a list of formatting keys present in string."""
    return [i[1] for i in Formatter().parse(string) if i[1] is not None]


def button_parser(markdown_note):
    note_data = ""
    buttons = []
    if markdown_note is None:
        return note_data, buttons
    if markdown_note.startswith("/") or markdown_note.startswith("!"):
        args = markdown_note.split(None, 2)
        markdown_note = args[2]
    prev = 0
    for match in BTN_URL_REGEX.finditer(markdown_note):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and markdown_note[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        if n_escapes % 2 == 0:
            if bool(match.group(4)) and buttons:
                buttons[-1].append(
                    InlineKeyboardButton(text=match.group(2), url=match.group(3))
                )
            else:
                buttons.append(
                    [InlineKeyboardButton(text=match.group(2), url=match.group(3))]
                )
            note_data += markdown_note[prev : match.start(1)]
            prev = match.end(1)

        else:
            note_data += markdown_note[prev:to_check]
            prev = match.start(1) - 1

    note_data += markdown_note[prev:]

    return note_data, buttons


@WhiterX.on_message(filters.command("admins", Config.TRIGGER) & filters.group)
async def mentionadmins(c: WhiterX, m: Message):
    if m.chat.type == ChatType.PRIVATE:
        await m.reply("Usage only in groups, no in private!!")
        return
    mention = ""
    async for i in m.chat.get_members(m.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        if not (i.user.is_deleted or i.privileges.is_anonymous):
            mention += f"{i.user.mention}\n"
    await c.send_message(
        m.chat.id,
        (await tld(m.chat.id, "ADMINS_STRING")).format(chat_title=m.chat.title, admins_list=mention),
    )

@WhiterX.on_message(filters.command("warn", Config.TRIGGER))
@disableable_dec("warn")
async def warn_users(c: WhiterX, m: Message):
    chat_id = m.chat.id
    if not await is_admin(chat_id, m.from_user.id):
        return await m.reply(await tld(m.chat.id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, m.from_user.id, "can_restrict_members"):
        await m.reply(await tld(chat_id, "NO_BAN_USER"))
        return
    cmd = len(m.text)
    replied = m.reply_to_message
    reason = ""
    if replied:
        id_ = replied.from_user.id
        if cmd > 5:
            _, reason = m.text.split(maxsplit=1)
    elif cmd > 5:
        _, args = m.text.split(maxsplit=1)
        if " " in args:
            id_, reason = args.split(" ", maxsplit=1)
        else:
            id_ = args
    else:
        await m.reply(await tld(chat_id, "BANS_NOT_ESPECIFIED_USER"))
        return
    try:
        user = await c.get_users(id_)
        user_id = user.id
        mention = user.mention
    except (UsernameInvalid, PeerIdInvalid, UserIdInvalid):
        await m.reply(
            await tld(m.chat.id, "BANS_ID_INVALID")
        )
        return
    if await is_self(user_id):
        await m.reply(await tld(chat_id, "BAN_MY_SELF"))
        return 
    if is_dev(user_id):
        await m.reply(await tld(chat_id, "BAN_IN_DEV"))
        return
    if await is_admin(chat_id, user_id):
        await m.reply(await tld(chat_id, "BAN_IN_ADMIN"))
        return
    if not await check_bot_rights(chat_id, "can_restrict_members"):
        await m.reply(await tld(chat_id, "NO_BAN_BOT"))
        return
    
    if await WARNS_LIMIT.find_one({"chat_id": m.chat.id}):
        LIMIT = await WARNS_LIMIT.find_one({"chat_id": m.chat.id})
        warns_limit = LIMIT["limit"]
    else:
        warns_limit = 3
    
    if await WARN_ACTION.find_one({"chat_id": m.chat.id}):
        ACTION = await WARN_ACTION.find_one({"chat_id": m.chat.id})
        warn_action = ACTION["action"]
    else:
        warn_action = "ban"
        
    await DB_WARNS.insert_one({"chat_id": m.chat.id, "user_id": user_id, "warn_id": str(uuid.uuid4()), "reason": reason or None})
    
    user_warns = await DB_WARNS.count_documents({"chat_id": m.chat.id, "user_id": user_id})
    
    if user_warns >= warns_limit:
        if warn_action == "ban":
            await m.chat.ban_member(user_id)
            await m.reply((await tld(chat_id, "WARNS_BANNED")).format(user_warns, warns_limit, mention))
        elif warn_action == "mute":
            await m.chat.restrict_member(user_id, ChatPermissions())
            await m.reply((await tld(chat_id, "WARNS_MUTED")).format(user_warns, warns_limit, mention))
        elif warn_action == "kick":
            await m.chat.ban_member(user_id)
            await m.chat.unban_member(user_id)
            await m.reply((await tld(chat_id, "WARNS_KICKED")).format(user_warns, warns_limit, mention))
        else:
            return
        await DB_WARNS.delete_many({"chat_id": m.chat.id, "user_id": user_id})
    else:
        keyboard = [[InlineKeyboardButton(await tld(chat_id, "RULES_WARN_BNT"), callback_data=f"rules|{user_id}"), InlineKeyboardButton(await tld(chat_id, "UNWARN_BNT"), callback_data=f"rm_warn|{user_id}")]]
        await m.reply((await tld(chat_id, "USER_WARNED")).format(mention, user_warns, warns_limit, reason or None), reply_markup=InlineKeyboardMarkup(keyboard))
        
@WhiterX.on_message(filters.command("unwarn", Config.TRIGGER))
@disableable_dec("unwarn")
async def unwarn_users(c: WhiterX, m: Message):
    chat_id = m.chat.id
    if not await is_admin(chat_id, m.from_user.id):
        return await m.reply(await tld(m.chat.id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, m.from_user.id, "can_restrict_members"):
        await m.reply(await tld(chat_id, "NO_BAN_USER"))
        return

    cmd = len(m.text)
    replied = m.reply_to_message
    reason = ""
    if replied:
        id_ = replied.from_user.id
        if cmd > 7:
            _, reason = m.text.split(maxsplit=1)
    elif cmd > 7:
        _, args = m.text.split(maxsplit=1)
        if " " in args:
            id_, reason = args.split(" ", maxsplit=1)
        else:
            id_ = args
    else:
        await m.reply(await tld(chat_id, "BANS_NOT_ESPECIFIED_USER"))
        return
    try:
        user = await c.get_users(id_)
        user_id = user.id
        mention = user.mention
    except (UsernameInvalid, PeerIdInvalid, UserIdInvalid):
        await m.reply(
            await tld(chat_id, "PEER_ID_INVALID")
        )
        return
    if await is_self(user_id):
        await m.reply(await tld(chat_id, "BAN_MY_SELF"))
        return 
    if is_dev(user_id):
        await m.reply(await tld(chat_id, "BAN_IN_DEV"))
        return
    if await is_admin(chat_id, user_id):
        await m.reply(await tld(chat_id, "BAN_IN_ADMIN"))
        return
    if not await check_bot_rights(chat_id, "can_restrict_members"):
        await m.reply(await tld(chat_id, "NO_BAN_BOT"))
        return
    
    #delete one warn--user
    if await DB_WARNS.find_one({"chat_id": m.chat.id, "user_id": user_id}):
        await DB_WARNS.delete_one({"chat_id": m.chat.id, "user_id": user_id})
        await m.reply(await tld(chat_id, "UNWARNED"))
    else:
        await m.reply(await tld(chat_id, "USER_NOT_WARNS"))
        
        
@WhiterX.on_message(filters.command(["setwarnslimit", "setwarnlimit"], Config.TRIGGER))
async def set_warns_limit(c: WhiterX, m: Message):
    if not await is_admin(m.chat.id, m.from_user.id):
        return await m.reply(await tld(m.chat.id, "USER_NO_ADMIN"))
    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
    if len(m.command) == 1:
        await m.reply("Eu preciso de um argumento.")
        return
    try:
        warns_limit = int(m.command[1])
    except ValueError:
        return await m.reply("Esse limite não é valido.")
    await WARNS_LIMIT.update_one({"chat_id": m.chat.id}, {"$set": {"limit": warns_limit}}, upsert=True)
    await m.reply(f"<i>O limite de advertências foi alterado para {warns_limit}</i>")

    
@WhiterX.on_message(filters.command(["setwarnmode", "setwarnaction"], Config.TRIGGER))
async def set_warns_mode(c: WhiterX, m: Message):
    if not await is_admin(m.chat.id, m.from_user.id):
        return await m.reply(await tld(m.chat.id, "USER_NO_ADMIN"))
    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
    
    if len(m.text.split()) > 1:
        if not m.command[1] in ("ban", "mute", "kick"):
            return await m.reply_text("Esse argumento não é valido.")

        warn_action_txt = m.command[1]
        
            
        await WARN_ACTION.update_one({"chat_id": m.chat.id}, {"$set": {"action": warn_action_txt}}, upsert=True)
       
        await m.reply_text(
        f"A ação de advertências do chat foi alterado para: {warn_action_txt}"
    )
    else:
        if await WARN_ACTION.find_one({"chat_id": m.chat.id}):
            r = await WARN_ACTION.find_one({"chat_id": m.chat.id})
            warn_act = r["action"]
        else:
            warn_act = "ban"
        await m.reply_text("A ação atual de advertências é: {action}".format(action=warn_act))
        

@WhiterX.on_message(filters.command("warns", Config.TRIGGER))
@disableable_dec("warns")
async def warns_from_users(c: WhiterX, m: Message):
    chat_id = m.chat.id
    if not await is_admin(chat_id, m.from_user.id):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, m.from_user.id, "can_restrict_members"):
        return await m.reply(await tld(chat_id, "NO_BAN_USER"))
    
    cmd = len(m.text)
    replied = m.reply_to_message
    reason = ""
    if replied:
        id_ = replied.from_user.id
        if cmd > 6:
            _, reason = m.text.split(maxsplit=1)
    elif cmd > 6:
        _, args = m.text.split(maxsplit=1)
        if " " in args:
            id_, reason = args.split(" ", maxsplit=1)
        else:
            id_ = args
    else:
        id_ = m.from_user.id
       
    try:
        user = await c.get_users(id_)
        user_id = user.id
        mention = user.mention
    except (UsernameInvalid, PeerIdInvalid, UserIdInvalid):
        await m.reply(
            await tld(chat_id, "PEER_ID_INVALID")
        )
        return
    
    if not await check_bot_rights(chat_id, "can_restrict_members"):
        await m.reply(await tld(chat_id, "NO_BAN_BOT"))
        return
    
    if not await DB_WARNS.find_one({"chat_id": m.chat.id, "user_id": user_id}):
        return await m.reply((await tld(chat_id, "ATT_USER_NO_WARNS")).format(mention))
    
    if await WARNS_LIMIT.find_one({"chat_id": m.chat.id}):
        res = await WARNS_LIMIT.find_one({"chat_id": m.chat.id})
        warns_limit = res["limit"]
    else:
        warns_limit = 3
        
    user_warns = await DB_WARNS.count_documents({"chat_id": m.chat.id, "user_id": user_id})
    
    await m.reply((await tld(chat_id, "ATT_USER_WARNS")).format(mention, user_warns, warns_limit))

    
@WhiterX.on_callback_query(filters.regex(pattern=r"^rules\|(.*)"))
async def warn_rules(c: WhiterX, cb: CallbackQuery):
    try:
        data, userid = cb.data.split("|")
    except ValueError:
        return print(cb.data)
    if cb.from_user.id != int(userid):
        await cb.answer(await tld(cb.message.chat.id, "NO_RULES_WARN_YOU"), show_alert=True)
        return
    chat_id = cb.message.chat.id
    resp = await RULES_DB.find_one()
    if resp:
        RULES = resp["_rules"]
        text = (await tld(chat_id, "RULES")).format(cb.message.chat.title, RULES)
    else:
        text = await tld(chat_id, "NO_RULES")
    await cb.edit_message_text(text=text, disable_web_page_preview=True)

    
@WhiterX.on_callback_query(filters.regex(pattern=r"^rm_warn\|(.*)"))
async def unwarn(c: WhiterX, cb: CallbackQuery):
    data, id_ = cb.data.split("|")
    chat_id = cb.message.chat.id
    mention_ = cb.from_user.mention
    uid = cb.from_user.id
    if not await is_admin(chat_id, uid):
        return await cb.answer(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, uid, "can_restrict_members"):
        return await cb.answer(await tld(chat_id, "NO_BAN_USER"), show_alert=True)
    try:
        user = await c.get_users(id_)
        user_id = user.id
        mention = user.mention
    except (UsernameInvalid, PeerIdInvalid, UserIdInvalid):
        await cb.message.reply(
            await tld(cb.message.chat.id, "PEER_ID_INVALID")
        )
    await unwarn_bnt(chat_id, user_id)
    #send as message
    await cb.edit_message_text(text=(await tld(chat_id, "UNWARNED_CALLBACKQUERY")).format(mention, mention_), disable_web_page_preview=True)
    
##
### Goodbyes

@WhiterX.on_message(filters.command("setgoodbye", Config.TRIGGER))
async def set_goodbye_message(c: WhiterX, m: Message):
    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
    if len(m.text.split()) > 1:
        message = m.text.html.split(None, 1)[1]
        try:
            # Try to send message with default parameters
            sent = await m.reply_text(
                message.format(
                    id=m.from_user.id,
                    username=m.from_user.username,
                    mention=m.from_user.mention,
                    first_name=m.from_user.first_name,
                    first=m.from_user.first_name,
                    # full_name and name are the same
                    full_name=m.from_user.first_name,
                    name=m.from_user.first_name,
                    # title and chat_title are the same
                    title=m.chat.title,
                    chat_title=m.chat.title,
                    count=(await c.get_chat_members_count(m.chat.id)),
                )
            )
            await asyncio.sleep(0.7)
        except (KeyError, BadRequest) as e:
            await m.reply_text(
                "<b>Erro:</b> {error}".format(
                    error=e.__class__.__name__ + ": " + str(e)
                )
            )
        else:
            await GOODBYES_DB.update_one({"chat_id": m.chat.id}, {"$set": {"msg": message}}, upsert=True)
            await sent.edit_text(
                "Mensagem de Despedida Alterada em {chat_title}".format(chat_title=m.chat.title)
            )
    else:
        await m.reply_text(
            "De um argumento exemplo: /setgoodbye Olá {mention}",
            disable_web_page_preview=True,
        )

@WhiterX.on_message(filters.command("goodbye on", Config.TRIGGER) & filters.group)
async def enable_welcome_message(c: WhiterX, m: Message):
    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
    await GOODBYES_STATUS.update_one({"chat_id": m.chat.id}, {"$set": {"status": True}}, upsert=True)
    await m.reply_text("Mensagem de Despedida agora está Ativada.")
    
    
@WhiterX.on_message(filters.command("goodbye off", Config.TRIGGER) & filters.group)
async def disable_goodbye_message(c: WhiterX, m: Message):
    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
    await GOODBYES_STATUS.update_one({"chat_id": m.chat.id}, {"$set": {"status": False}}, upsert=True)
    await m.reply_text("Mensagem de Despedida agora está Desativada.")
    
    
@WhiterX.on_message(filters.command("goodbye", Config.TRIGGER) & filters.group)
async def goodbye_status(c: WhiterX, m: Message):
    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
    await m.reply_text("Dê um argumento exemplo: /goodbye on/off")
 

@WhiterX.on_message(filters.left_chat_member & filters.group)
async def greet_left_members(c: WhiterX, m: Message):
    members = m.left_chat_member
    chat_title = m.chat.title
    first_name = members.first_name
    full_name = members.first_name + " " + members.last_name if members.last_name else members.first_name
    
    user_id = members.id
    username = "@" + members.username if members.username else members.mention
    
    mention = members.mention

    if not m.from_user.is_bot:
        goodbye_enabled = await GOODBYES_STATUS.find_one({"chat_id": m.chat.id, "status": True})
        goodbye_pack = await GOODBYES_DB.find_one({"chat_id": m.chat.id})
        if goodbye_enabled:
            if not goodbye_pack:
                welcome = "Nice knowing ya!"
            else:
                welcome = goodbye_pack["msg"]
            if "count" in get_format_keys(welcome):
                count = await c.get_chat_members_count(m.chat.id)
            else:
                count = 0

            goodbye = welcome.format(
                id=user_id,
                username=username,
                mention=mention,
                first_name=first_name,
                first=first_name,
                # full_name and name are the same
                full_name=full_name,
                name=full_name,
                # title and chat_title are the same
                title=chat_title,
                chat_title=chat_title,
                count=count,
            )
            goodbye, buttons = button_parser(welcome)
            await m.reply_text(
                goodbye,
                disable_web_page_preview=True,
                reply_markup=(
                    InlineKeyboardMarkup(buttons)
                    if len(buttons) != 0
                    else None
                ),
            )

            
@WhiterX.on_message(filters.command("getgoodbye", Config.TRIGGER))
async def get_welcome(c: WhiterX, m: Message):
    resp = await GOODBYES_DB.find_one({"chat_id": m.chat.id})
    if resp:
        goodbye = resp["msg"]
    else:
        goodbye = "Nice knowing ya!"
        
    await m.reply(goodbye)

    
@WhiterX.on_message(filters.command("resetgoodbye", Config.TRIGGER))
async def rm_welcome(c: WhiterX, m: Message):
    r = await GOODBYES_DB.find_one({"chat_id": m.chat.id})
    if r:
        await GOODBYES_DB.delete_many({"chat_id": m.chat.id})
        await m.reply("A mensagem despedida foi resetada!") 
    else:
        return await m.reply("Nenhuma mensagem de despedida foi definida.")
    
##
### Welcomes

@WhiterX.on_message(filters.command("setwelcome", Config.TRIGGER))
async def set_welcome_message(c: WhiterX, m: Message):
    if not await find_user(m.from_user.id):
        await add_user(m.from_user.id)
    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
   
    if len(m.text.split()) > 1:
        message = m.text.html.split(None, 1)[1]
        try:
            # Try to send message with default parameters
            sent = await m.reply_text(
                message.format(
                    id=m.from_user.id,
                    username=m.from_user.username,
                    mention=m.from_user.mention,
                    first_name=m.from_user.first_name,
                    first=m.from_user.first_name,
                    # full_name and name are the same
                    full_name=m.from_user.first_name,
                    name=m.from_user.first_name,
                    # title and chat_title are the same
                    title=m.chat.title,
                    chat_title=m.chat.title,
                    count=(await c.get_chat_members_count(m.chat.id)),
                )
            )
            await asyncio.sleep(0.7)
        except (KeyError, BadRequest) as e:
            await m.reply_text(
                "<b>Erro:</b> {error}".format(
                    error=e.__class__.__name__ + ": " + str(e)
                )
            )
        else:
            await DB_WELCOME.update_one({"chat_id": m.chat.id}, {"$set": {"msg": message}}, upsert=True)
            await sent.edit_text(
                "Boas Vindas Alterada em {chat_title}".format(chat_title=m.chat.title)
            )
    else:
        await m.reply_text(
            "De um argumento exemplo: /setwelcome Olá {mention}",
            disable_web_page_preview=True,
        )

@WhiterX.on_message(filters.command(["welcome on", "welcome true"], Config.TRIGGER) & filters.group)
async def enable_welcome_message(c: WhiterX, m: Message):
    if not await find_user(m.from_user.id):
        await add_user(m.from_user.id)

    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
    await WELCOME_STATUS.update_one({"chat_id": m.chat.id}, {"$set": {"status": True}}, upsert=True)
    await m.reply_text("Boas Vindas agora está Ativadas.")
    
    
@WhiterX.on_message(filters.command(["welcome off", "welcome false"], Config.TRIGGER) & filters.group)
async def disable_welcome_message(c: WhiterX, m: Message):
    if not await find_user(m.from_user.id):
        await add_user(m.from_user.id)
    
    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
    await WELCOME_STATUS.update_one({"chat_id": m.chat.id}, {"$set": {"status": False}}, upsert=True)
    await m.reply_text("Boas Vindas agora está Desativadas.")
    
    
@WhiterX.on_message(filters.command("welcome", Config.TRIGGER) & filters.group)
async def welcome_(c: WhiterX, m: Message):
    if not await find_user(m.from_user.id):
        await add_user(m.from_user.id)
    if not await check_rights(m.chat.id, m.from_user.id, "can_change_info"):
        return
    await m.reply_text("Dê um argumento exemplo: /welcome on/off/true/false")
 

@WhiterX.on_message(filters.new_chat_members & filters.group)
async def greet_new_members(c: WhiterX, m: Message):
    members = m.new_chat_members
    chat_title = m.chat.title
    first_name = ", ".join(map(lambda a: a.first_name, members))
    full_name = ", ".join(
        map(lambda a: a.first_name + " " + (a.last_name or ""), members)
    )
    user_id = ", ".join(map(lambda a: str(a.id), members))
    username = ", ".join(
        map(lambda a: "@" + a.username if a.username else a.mention, members)
    )
    
    #Check if is GBANNED
    if await check_antispam(m.chat.id):
        await check_ban(m, m.chat.id, user_id)
        
    mention = ", ".join(map(lambda a: a.mention, members))
    
    if not m.from_user.is_bot:
        welcome_enabled = await WELCOME_STATUS.find_one({"chat_id": m.chat.id, "status": True})
        welcome_pack = await DB_WELCOME.find_one({"chat_id": m.chat.id})
        captcha_pack = await CAPTCHA_DB.find_one({"chat_id": m.chat.id})
        if welcome_enabled:
            if not welcome_pack:
                welcome = "Hey {first_name}, how are you?"
            else:
                welcome = welcome_pack["msg"]
            if "count" in get_format_keys(welcome):
                count = await c.get_chat_members_count(m.chat.id)
            else:
                count = 0

            welcome = welcome.format(
                id=user_id,
                username=username,
                mention=mention,
                first_name=first_name,
                first=first_name,
                # full_name and name are the same
                full_name=full_name,
                name=full_name,
                # title and chat_title are the same
                title=chat_title,
                chat_title=chat_title,
                count=count,
            )

            if not await find_user(user_id):
                await add_user(user_id)
            
            welcome, welcome_buttons = button_parser(welcome)
            if await CAPTCHA_DB.find_one({"chat_id": m.chat.id, "status": True}):
                if await is_admin(m.chat.id, user_id):
                    #send message for admin 
                    await m.reply_text(
                        welcome,
                        disable_web_page_preview=True,
                        reply_markup=(
                            InlineKeyboardMarkup(welcome_buttons)
                            if len(welcome_buttons) != 0
                            else None
                        ),
                    )
                    return
                if await check_bot_rights(m.chat.id, "can_restrict_members"):
                    welcome_buttons += [[InlineKeyboardButton("Clique aqui para ser desmutado", callback_data=f"cptcha|{user_id}")]]
                    try:
                        await c.restrict_chat_member(m.chat.id, user_id, ChatPermissions())
                    except Exception as e:
                        await m.reply("Não foi possivel mutar o usúario devido a: {}".format(e))
            #send message
            await m.reply_text(
                welcome,
                disable_web_page_preview=True,
                reply_markup=(
                    InlineKeyboardMarkup(welcome_buttons)
                    if len(welcome_buttons) != 0
                    else None
                ),
            )

    
@WhiterX.on_message(filters.command("getwelcome", Config.TRIGGER))
async def get_welcome(c: WhiterX, m: Message):
    if not await find_user(m.from_user.id):
        await add_user(m.from_user.id)
    resp = await DB_WELCOME.find_one({"chat_id": m.chat.id})
    if resp:
        welcome = resp["msg"]
    else:
        welcome = "Hey {first}, how are you?"
        
    await m.reply(welcome)

    
@WhiterX.on_message(filters.command("resetwelcome", Config.TRIGGER))
async def rm_welcome(c: WhiterX, m: Message):
    if not await find_user(m.from_user.id):
        await add_user(m.from_user.id)
    r = await DB_WELCOME.find_one()
    if r:
        await DB_WELCOME.delete_many({"chat_id": m.chat.id})
        await m.reply("A mensagem de boas vindas foi resetada!") 
    else:
        return await m.reply("Nenhuma mensagem de boas vindas foi definida.")

    
@WhiterX.on_callback_query(filters.regex(pattern=r"^cptcha\|(.*)"))
async def warn_rules(c: WhiterX, cb: CallbackQuery):
    try:
        data, userid = cb.data.split("|")
    except ValueError:
        return print(cb.data)
    
    if cb.from_user.id != int(userid):
        await cb.answer("Isso não é para você!")
        return
    if await is_admin(cb.message.chat.id, userid):
        await cb.answer("Você não precisa mais compretar o captcha já que és administrador.")
        return
    response = await DB_WELCOME.find_one({"chat_id": cb.message.chat.id})
    if response:
        msg = response["msg"]
    else:
        msg = "Hey {first}, How are you?"
    if "count" in get_format_keys(msg):
        count = await c.get_chat_members_count(cb.message.chat.id)
    else:
        count = 0

    first = cb.from_user.first_name
    mention = cb.from_user.mention
    user_id = cb.from_user.id
    chat_title = cb.message.chat.title
    full_name = cb.from_user.first_name + " " + cb.from_user.last_name if cb.from_user.last_name else cb.from_user.first_name
    username = "@" + cb.from_user.username if cb.from_user.username else cb.from_user.mention
    try:
        msg = msg.format(
            id=user_id,
            username=username,
            mention=mention,
            first_name=first,
            first=first,
            # full_name and name are the same
            full_name=full_name,
            name=full_name,
            # title and chat_title are the same
            title=chat_title,
            chat_title=chat_title,
            count=count,
        )
    except (KeyError, BadRequest) as e:
        await cb.message.edit_text(
            "<b>Erro:</b> {error}".format(
                error=e.__class__.__name__ + ": " + str(e)
            )
        )
    captcha_welcome, buttons = button_parser(msg)
    try:
        await c.unban_chat_member(cb.message.chat.id, userid)
        await cb.answer("Parabéns você completou o captcha, Agora você pode falar no chat!", show_alert=True)
        await cb.message.edit_text(
            captcha_welcome,
            disable_web_page_preview=True,
            reply_markup=(
                InlineKeyboardMarkup(buttons)
                if len(buttons) != 0
                else None
            ),
        )
    except Exception as e:
        return await cb.answer("Não foi possivel completar o captcha devido a: {}".format(e))

    
@WhiterX.on_message(filters.command("captcha on", Config.TRIGGER) & filters.group)
async def enable_captcha(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM"))
    
    await CAPTCHA_DB.update_one({"chat_id": m.chat.id}, {"$set": {"status": True}}, upsert=True)
    await m.reply_text("Captcha agora está Ativado.")

    
@WhiterX.on_message(filters.command("captcha off", Config.TRIGGER) & filters.group)
async def disable_captcha(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id
    
    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM"))
    
    await CAPTCHA_DB.update_one({"chat_id": chat_id}, {"$set": {"status": False}}, upsert=True)
    await m.reply_text("Captcha agora está Desativado.")
    

@WhiterX.on_message(filters.command("captcha", Config.TRIGGER) & filters.group)
async def captcha(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id
    
    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM"))
    
    await m.reply_text("Dê um argumento exemplo: /captcha on/off")
 
@WhiterX.on_message(filters.command(["save", "savenote", "note"], Config.TRIGGER))
@disableable_dec("save")
async def save_notes(c: WhiterX, m: Message):
    chat_id = m.chat.id
    user_id = m.from_user.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, user_id):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"), quote=True)
    if not await check_rights(chat_id, user_id, "can_change_info"):
        return await m.reply(await tld(chat_id, "NOTES_NO_PERM"), quote=True)
    if m.reply_to_message is None and len(input_str(m)) < 2:
        await m.reply_text(await tld(chat_id, "NOTES_NOT_NAME"), quote=True)
        return
    
    args = m.text.html.split(maxsplit=1)
    split_text = f"{args[1]}"
    trigger = split_text.lower()
    if trigger[0] == '#':
        trigger = trigger[1:]
        
    sym = None
    if any((sym := s) in trigger for s in RESTRICTED_SYMBOLS_IN_NOTENAMES):
        await m.reply("O nome da nota não deve ter o caractere {}".format(sym))
        return

    
    if m.reply_to_message and m.reply_to_message.photo:
        file_id = m.reply_to_message.photo.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        note_type = "photo"
    elif m.reply_to_message and m.reply_to_message.document:
        file_id = m.reply_to_message.document.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        note_type = "document"
    elif m.reply_to_message and m.reply_to_message.video:
        file_id = m.reply_to_message.video.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        note_type = "video"
    elif m.reply_to_message and m.reply_to_message.audio:
        file_id = m.reply_to_message.audio.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        note_type = "audio"
    elif m.reply_to_message and m.reply_to_message.voice:
        file_id = m.reply_to_message.voice.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        note_type = "voice"
    elif m.reply_to_message and m.reply_to_message.animation:
        file_id = m.reply_to_message.animation.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        note_type = "animation"
    elif m.reply_to_message and m.reply_to_message.sticker:
        file_id = m.reply_to_message.sticker.file_id
        raw_data = split_text[1] if len(split_text) > 1 else None
        note_type = "sticker"
    else:
        if m.reply_to_message and m.reply_to_message.text:
            file_id = None
            raw_data = m.reply_to_message.text
            note_type = "text"
        else:
            await m.reply(await tld(m.chat.id, "NOTES_NO_REPLY"))
            return

    check_note = await DB_NOTES.find_one({"chat_id": chat_id, "name": trigger})
    if check_note:
        await DB_NOTES.update_one({"chat_id": chat_id, "name": trigger}, {"$set": {"raw_data": raw_data, "file_id": file_id, "type": note_type}})
    else:
        await DB_NOTES.insert_one({"chat_id": chat_id, "name": trigger, "raw_data": raw_data, "file_id": file_id, "type": note_type})
    await m.reply((await tld(chat_id, "NOTES_SAVED")).format(trigger))

@WhiterX.on_message(filters.command("notes", Config.TRIGGER) & filters.group)
@disableable_dec("notes")
async def get_all_chat_note(c: WhiterX, m: Message):
    chat_id = m.chat.id
    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))
    reply_text = (await tld(chat_id, "NOTES_LIST")).format(m.chat.title)
    all_notes = DB_NOTES.find({"chat_id": chat_id})          
    async for note_s in all_notes:
        keyword = note_s["name"]
        reply_text += f" - <code>#{keyword}</code> \n"
    if not await DB_NOTES.find_one({"chat_id": chat_id}):
        await m.reply_text(await tld(chat_id, "NOTES_NOT_FOUND"), quote=True)
    else:
        reply_text += await tld(chat_id, "NOTES_SUB_LIST")
        await m.reply_text(reply_text, quote=True)

@WhiterX.on_message(filters.command(["rmnote", "delnote"]))
@disableable_dec("delnote")
async def rmnote(c: WhiterX, m: Message):
    args = m.text.html.split(maxsplit=1)
    trigger = args[1].lower()
    chat_id = m.chat.id
    check_admin = m.chat.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NOTES_NO_PERM"))

    check_note = await DB_NOTES.find_one({"chat_id": chat_id, "name": trigger})
    if check_note:
        await DB_NOTES.delete_one({"chat_id": chat_id, "name": trigger})
        await m.reply_text(
            (await tld(m.chat.id, "NOTES_REMOVED")).format(trigger), quote=True
        )
    else:
        await m.reply_text(
            (await tld(m.chat.id, "NOTES_REMOVE_NOT_FOUND")).format(trigger), quote=True
        )

        
@WhiterX.on_message(filters.command(["resetnotes", "clearnotes"]))
@disableable_dec("resetnotes")
async def clear_notes(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NOTES_NO_PERM"))

    check_note = await DB_NOTES.find_one({"chat_id": chat_id})
    if check_note:
        await DB_NOTES.delete_many({"chat_id": chat_id})
        await m.reply_text(
            "Todas as notas desse chat foram apagadas.", quote=True
        )
    else:
        await m.reply_text(
            "O grupo não tem notas.", quote=True
        )        

async def serve_note(c: WhiterX, m: Message, txt):
    chat_id = m.chat.id
    text = txt

    all_notes = DB_NOTES.find({"chat_id": chat_id})
    async for note_s in all_notes:
        keyword = note_s["name"]
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            data, button = button_parser(note_s["raw_data"])
            if note_s["type"] == "text":
                await m.reply_text(
                    data,
                    quote=True,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif note_s["type"] == "photo":
                await m.reply_photo(
                    note_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif note_s["type"] == "document":
                await m.reply_document(
                    note_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif note_s["type"] == "video":
                await m.reply_video(
                    note_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif note_s["type"] == "audio":
                await m.reply_audio(
                    note_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif note_s["type"] == "voice":
                await m.reply_voice(
                    note_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif note_s["type"] == "animation":
                await m.reply_animation(
                    note_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif note_s["type"] == "sticker":
                await m.reply_sticker(
                    note_s["file_id"],
                    quote=True,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
                
                
@WhiterX.on_message(filters.command("get") & filters.group)
async def note_by_get_command(c: WhiterX, m: Message):
    note_data = " ".join(m.command[1:])
    targeted_message = m.reply_to_message or m
    await serve_note(c, targeted_message, txt=note_data)

    
@WhiterX.on_message(filters.regex(r"^#[^\s]+") & filters.group)
async def note_by_hashtag(c: WhiterX, m: Message):
    note_data = m.text[1:]
    targeted_message = m.reply_to_message or m
    await serve_note(c, targeted_message, txt=note_data)


@WhiterX.on_message(filters.command(["filter", "savefilter", "addfilter"], Config.TRIGGER))
@disableable_dec("filter")
async def save_notes(c: WhiterX, m: Message):
    chat_id = m.chat.id
    user_id = m.from_user.id

    if not await check_rights(chat_id, user_id, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM"), quote=True)
    
    if m.reply_to_message is None and len(input_str(m)) < 2:
        await m.reply_text("Você Precisa dar um nome ao filtro.", quote=True)
        return
    
    args = m.text.html.split(maxsplit=1)
    split_text = f"{args[1]}"
    trigger = split_text.lower()
    
    
    if m.reply_to_message and m.reply_to_message.photo:
        file_id = m.reply_to_message.photo.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        filter_type = "photo"
    elif m.reply_to_message and m.reply_to_message.document:
        file_id = m.reply_to_message.document.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        filter_type = "document"
    elif m.reply_to_message and m.reply_to_message.video:
        file_id = m.reply_to_message.video.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        filter_type = "video"
    elif m.reply_to_message and m.reply_to_message.audio:
        file_id = m.reply_to_message.audio.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        filter_type = "audio"
    elif m.reply_to_message and m.reply_to_message.voice:
        file_id = m.reply_to_message.voice.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        filter_type = "voice"
    elif m.reply_to_message and m.reply_to_message.animation:
        file_id = m.reply_to_message.animation.file_id
        raw_data = (
            m.reply_to_message.caption.html
            if m.reply_to_message.caption is not None
            else None
        )
        filter_type = "animation"
    elif m.reply_to_message and m.reply_to_message.sticker:
        file_id = m.reply_to_message.sticker.file_id
        raw_data = split_text[1] if len(split_text) > 1 else None
        filter_type = "sticker"
    else:
        if m.reply_to_message and m.reply_to_message.text:
            file_id = None
            raw_data = m.reply_to_message.text
            filter_type = "text"
        else:
            await m.reply("<i>Responda algo para salvar o filtro.</i>")
            return

    await DB_FILTERS.update_one({"chat_id": chat_id, "name": trigger}, {"$set": {"raw_data": raw_data, "file_id": file_id, "type": filter_type}}, upsert=True)
    await m.reply("Filtro {} foi adicionado em <b>{}.</b>".format(trigger, m.chat.title))
    await m.stop_propagation()


@WhiterX.on_message(filters.command("filters", Config.TRIGGER) & filters.group)
@disableable_dec("filters")
async def get_all_chat_note(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM"))

    reply_text = "<b>Lista de filtros em {}:</b>\n\n".format(m.chat.title)
    all_filters = DB_FILTERS.find({"chat_id": chat_id})          
    async for filter_s in all_filters:
        keyword = filter_s["name"]
        reply_text += f" • <code>{keyword}</code> \n"
    if not await DB_FILTERS.find_one({"chat_id": chat_id}):
        await m.reply_text("<i>Esse chat não tem filtros.</i>", quote=True)
    else:
        await m.reply_text(reply_text, quote=True)
    await m.stop_propagation()
        
        
@WhiterX.on_message(filters.command(["rmfilter", "delfilter", "stop"], Config.TRIGGER))
@disableable_dec("stop")
async def rmnote(c: WhiterX, m: Message):
    args = m.text.html.split(maxsplit=1)
    trigger = args[1].lower()
    chat_id = m.chat.id
    check_admin = m.from_user.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM"))

    check_note = await DB_FILTERS.find_one({"chat_id": chat_id, "name": trigger})
    if check_note:
        await DB_FILTERS.delete_many({"chat_id": chat_id, "name": trigger})
        await m.reply_text(
            "Filtro {} Removido em {}".format(trigger, m.chat.title), quote=True
        )
    else:
        await m.reply_text(
            "Esse não é um filtro ativo - use o comando /filters para todos os filtros ativos.".format(trigger), quote=True
        )
    await m.stop_propagation()

        
@WhiterX.on_message(filters.command(["resetfilters", "clearfilters"]))
async def clear_notes(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM"))
    
    check_note = await DB_FILTERS.find_one({"chat_id": chat_id})
    if check_note:
        await db.delete_many({"chat_id": chat_id})
        await m.reply_text(
            "Todas os filtros desse chat foram apagadas.", quote=True
        )
    else:
        await m.reply_text(
            "O grupo não tem filtros.", quote=True
        )  
    await m.stop_propagation()


@WhiterX.on_message(
    (filters.group | filters.private) & filters.text & filters.incoming, group=group_filter
)
async def serve_filter(c: WhiterX, m: Message):
    chat_id = m.chat.id
    gp_title = m.chat.title
    
    if not m.chat.type == ChatType.PRIVATE:
        #Check if is GBANNED
        if await check_antispam(m.chat.id):
            await check_ban(m, m.chat.id, m.from_user.id)
        
    text = m.text
    target_msg = m.reply_to_message or m

    all_filters = DB_FILTERS.find({"chat_id": m.chat.id})
    async for filter_s in all_filters:
        keyword = filter_s["name"]
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            data, button = button_parser(filter_s["raw_data"])
            if filter_s["type"] == "text":
                await target_msg.reply_text(
                    data,
                    quote=True,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif filter_s["type"] == "photo":
                await target_msg.reply_photo(
                    filter_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif filter_s["type"] == "document":
                await target_msg.reply_document(
                    filter_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif filter_s["type"] == "video":
                await target_msg.reply_video(
                    filter_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif filter_s["type"] == "audio":
                await target_msg.reply_audio(
                    filter_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif filter_s["type"] == "voice":
                await target_msg.reply_voice(
                    filter_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif filter_s["type"] == "animation":
                await target_msg.reply_animation(
                    filter_s["file_id"],
                    quote=True,
                    caption=data if not None else None,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
            elif filter_s["type"] == "sticker":
                await target_msg.reply_sticker(
                    filter_s["file_id"],
                    quote=True,
                    reply_markup=InlineKeyboardMarkup(button)
                    if len(button) != 0
                    else None,
                )
    await m.stop_propagation()                
                


@WhiterX.on_message(filters.command("disable", Config.TRIGGER))
async def disble_cmd(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id  
    query = input_str(m)

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM"))
    else:
        if not query in DISABLABLE_CMDS:
            return await m.reply(await tld(chat_id, "NO_DISABLE_COMMAND"))
        else:
            found = await DB_DISABLEABLE.find_one({"chat_id": chat_id, "cmd": query})
            if found:
                return await m.reply(await tld(chat_id, "ALREADY_DISABLED_COMMAND"))
            else:
                dis_cmd = await DB_DISABLEABLE.insert_one({"chat_id": chat_id, "cmd": query})
                await m.reply((await tld(chat_id, "COMMAND_NOW_DISABLED")).format(query))
                

@WhiterX.on_message(filters.command("enable", Config.TRIGGER))
async def enable_cmd(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id  
    query = input_str(m)

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM")) 
    else:
        if not query in DISABLABLE_CMDS:
            return await m.reply(await tld(chat_id, "NO_ENABLE_COMMAND")) 
        else:
            found = await DB_DISABLEABLE.find_one({"chat_id": chat_id, "cmd": query})
            if found:
                dis_cmd = await DB_DISABLEABLE.delete_one({"chat_id": chat_id, "cmd": query})
                await m.reply((await tld(chat_id, "COMMAND_NOW_ENABLED")).format(query))
            else:
                return await m.reply(await tld(chat_id, "NO_DISABLED_COMMAND"))
                

@WhiterX.on_message(filters.command("disableable", Config.TRIGGER))
async def disableable(_, m: Message):
    chat_id = m.chat.id
    user_id = m.from_user.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, user_id):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, user_id, "can_restrict_members"):
        return await m.reply(await tld(chat_id, "NO_BAN_BOT"))
    
    text = await tld(chat_id, "DISABLEABLE_COMMANDS")
    for command in sorted(DISABLABLE_CMDS):
        text += f"• <code>{command}</code>\n"
    await m.reply(text)

@WhiterX.on_message(filters.command(["lock", "unlock"], Config.TRIGGER))
@disableable_dec("locks")
async def locks_func(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_change_info"):
        return await m.reply(await tld(chat_id, "NO_CHANGEINFO_PERM"))
    
    if len(m.command) != 2:
        return await m.reply_text("<i>Invalid argument; Visit help in section Admins</i>")

    parameter = m.text.strip().split(None, 1)[1].lower()
    state = m.command[0].lower()

    if parameter not in LOCK_TYPES and parameter != "all":
        return await m.reply_text("<i>Invalid argument; Visit help in section Admins</i>")

    permissions = await current_chat_permissions(chat_id)

    if parameter in LOCK_TYPES:
        await tg_lock(
            m,
            permissions,
            LOCK_TYPES[parameter],
            bool(state == "lock"),
        )
    elif parameter == "all" and state == "lock":
        await c.set_chat_permissions(chat_id, ChatPermissions())
        await m.reply_text(f"Locked Everything in {m.chat.title}")

    elif parameter == "all" and state == "unlock":
        await c.set_chat_permissions(
            chat_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False,
            ),
        )
        await m.reply(f"Unlocked Everything in {m.chat.title}")


@WhiterX.on_message(filters.command("locks", Config.TRIGGER))
@disableable_dec("locktypes")
async def locktypes(c: WhiterX, m: Message):
    chat_id = m.chat.id
    check_admin = m.from_user.id

    if m.chat.type == ChatType.PRIVATE:
        return await m.reply(await tld(chat_id, "ONLY_GROUPS"))

    if not await is_admin(chat_id, check_admin):
        return await m.reply(await tld(chat_id, "USER_NO_ADMIN"))
    if not await check_rights(chat_id, check_admin, "can_restrict_members"):
        return await m.reply(await tld(chat_id, "NO_BAN_BOT"))
    
    permissions = await current_chat_permissions(m.chat.id)

    if not permissions:
        return await m.reply_text("No Permissions.")

    perms = ""
    for i in permissions:
        perms += f"<i><b>{i}</b><i>\n"

    await m.reply_text(perms)

@WhiterX.on_message(filters.command(["cleanup", "zombies"], prefixes=["/", "!"]))
@disableable_dec("zombies")
async def cleanup(c: megux, m: Message):
    chat_id = m.chat.id
    if m.chat.type == ChatType.PRIVATE:
        await m.reply_text(await tld(chat_id, "ONLY_GROUPS"))
        return
    if not await check_bot_rights(chat_id, "can_restrict_members"):
        await m.reply(await tld(chat_id, "NO_BAN_BOT"))
        return 
    if await check_rights(chat_id, m.from_user.id, "can_restrict_members"): 
        count = 0
        sent = await m.reply_text(await tld(chat_id, "COM_1"))
        async for t in c.get_chat_members(chat_id=chat_id):
            if t.user.is_deleted:
                try:
                    await c.ban_chat_member(chat_id, t.user.id)
                    count += 1
                except BadRequest:
                    pass
                except Forbidden as e:
                    await m.reply_text(
                        f"<b>Erro:</b> <code>{e}</code>"
                    )
                    return await c.send_err("<b>Error!!</b> {}".format(e))
        if count:
            await sent.edit_text(
                (await tld(chat_id, "ZOMBIES_BAN")).format(count, m.chat.title)
            )
        else:
            await sent.edit_text(await tld(chat_id, "NO_ZOMBIES"))
    else:
        await m.reply_text(await tld(chat_id, "NO_RIGHTS_ZOMBIES"))