import asyncio
import html

from hydrogram import filters
from hydrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from hydrogram.enums import ChatMemberStatus

from whiterkang import WhiterX, Config
from whiterkang.helpers import input_str, is_dev, disableable_dec, add_fed, add_fed_chat, del_fed_chat, get_fed_by_id, get_fed_by_creator, get_fed_by_name, fed_post_log

@WhiterX.on_message(filters.command(["newfed", "fnew"], Config.TRIGGER))
@disableable_dec("newfed")
async def new_fed(c: WhiterX, m: Message):
    name_fed = input_str(m)
    user_id = m.from_user.id
    user_mention = m.from_user.mention

    if user_id == 1087968824:
        return await m.reply("You are in incognito mode! To use this command, disable it first.")
    
    if not name_fed:
        await m.reply("I need you to enter the name of the federation")
        return

    if len(name_fed) > 60:
        await m.reply("The name of the federation exceeded the 60 character limit!  Please enter a shorter name.")
        return
    
    if await get_fed_by_creator(user_id) and not is_dev(user_id):
        await m.reply("Users can only have 1 federation. So remove it and try creating the federation again!")
        return
    
    if await get_fed_by_name(name_fed):
        await m.reply("The federation name {} is already in use!".format(name_fed))
        return
    
    creator_id, fed_name, fed_id = await add_fed(name_fed, user_id)
    
    await m.reply(
        "<b>Congrats, you have successfully created a federation.</b>\n<b>Name:</b> {}\n<b>ID:</b> <code>{}</code>\n<b>Creator:</b> {} ({})\nUse <code>/fjoin {}</code> to connect federation to chat".format(fed_name, fed_id, user_mention, creator_id, fed_id)
    )
    await c.send_log(
        "<b>New federation.</b>\n<b>Name:</b> {}\n<b>ID:</b> <code>{}</code>\n<b>Creator:</b> {}".format(fed_name, fed_id, user_mention)
    )

@WhiterX.on_message(filters.command(["joinfed", "fjoin"], Config.TRIGGER))
@disableable_dec("joinfed")
async def join_fed(c: WhiterX, m: Message):
    fed_id = input_str(m)
    user_id = m.from_user.id
    chat_id = m.chat.id
    fed = await get_fed_by_id(fed_id)
    #Check Chat-Owner
    check_owner = await m.chat.get_member(user_id)
    if not check_owner.status in [ChatMemberStatus.OWNER]:
        await m.reply("<i>You must be the chat creator to be able to connect chat to a federation.")
        return
    
    # Assume Fed ID invalid
    if not fed:
        await m.reply("The given federation ID is invalid! Please give me a valid ID.")
        return
    
    # Assume chat already joined this/other fed
    if 'chats' in fed and chat_id in fed['chats']:
        await m.reply("This chat has already joined a federation! Please use /fleave to leave that federation")
        return
    
    await add_fed_chat(chat_id, fed_id)

    await m.reply("Great! Chat <b>{}</b> is now a part of <b>{}</b> federation!".format(
        m.chat.title, html.escape(fed['fed_name'], False))
    )

    await fed_post_log(
        fed, 
        "<b>Chat joined federation</b> #ChatJoined\n<b>Fed:</b> {} (<code>{}</code>)\n<b>Chat:</b> {} (<code>{}</code>)".format(
        fed['fed_name'],
        fed['fed_id'],
        m.chat.title,
        chat_id
    ))