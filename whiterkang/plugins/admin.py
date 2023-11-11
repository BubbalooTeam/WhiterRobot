from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter, ChatType


from whiterkang import WhiterX, Config
from whiterkang.helpers import tld

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
