# WhiterKang BOT
# Copyright (C) 2022 KuuhakuTeam
#
# This file is based of < https://github.com/KuuhakuTeam/YuunaRobot/ >
# PLease read the GNU v3.0 License Agreement in 
# <https://www.github.com/KuuhakuTeam/YuunaRobot/blob/master/LICENSE/>.

import time
import glob

from typing import Union
from importlib import import_module

from hydrogram import filters
from hydrogram.enums import ChatType
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ChatPrivileges,
)

from whiterkang import WhiterX, version, START_TIME, db
from whiterkang.helpers import time_formatter, add_user, find_user, add_lang, tld, find_gp, add_gp, require_admin

HELPABLE: list[str] = []
LANGS = ["en", "pt", "es"]

for modules in glob.glob("whiterkang/plugins/*.py"):
    imported_module = import_module((modules)[:-3].replace("/", "."))
    if hasattr(imported_module, "__help__"):
        HELPABLE.append((modules.replace("/", ".")).split(".")[-2])


@WhiterX.on_callback_query(filters.regex(pattern=r"^start_back$"))
@WhiterX.on_message(filters.command("start"))
async def start_(c: WhiterX, m: Union[Message, CallbackQuery]):
    msg = m if isinstance(m, Message) else m.message
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=await tld(msg.chat.id, "button_lang"), callback_data="lang_menu"),
            ],
            [
                InlineKeyboardButton(
                    text=await tld(msg.chat.id, "ABOUT_BNT"), callback_data="about"),
                InlineKeyboardButton(
                    text=await tld(msg.chat.id, "HELP_BNT"), callback_data="help_menu"),
            ],
        ]
    )
    msg = (await tld(msg.chat.id, "START")).format(m.from_user.first_name, c.me.first_name, c.me.username)
    if isinstance(m, Message):
        if not m.chat.type == ChatType.PRIVATE:
            if not await find_gp(m.chat.id):
                await add_gp(m)
            return await m.reply((await tld(m.chat.id, "START_NO_PRIVATE")).format(c.me.first_name))
        await c.send_message(m.chat.id, text=msg, reply_markup=keyboard)
        if not await find_user(m.from_user.id):
            await add_user(m.from_user.id)
    if isinstance(m, CallbackQuery):
        await m.edit_message_text(
            text=msg,
            reply_markup=keyboard
        )


@WhiterX.on_callback_query(filters.regex(pattern=r"about"))
async def about_menu(c: WhiterX, cb: CallbackQuery):
    keyboard = [
        [
            InlineKeyboardButton(await tld(cb.message.chat.id, "BACK_BNT"), "start_back"),
        ],
    ]
    text = (await tld(cb.message.chat.id, "ABOUT_TEXT")).format(version.__WhiterX_version__)
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)


@WhiterX.on_callback_query(filters.regex(pattern=r"^lang_menu$"))
async def infos(client: WhiterX, cb: CallbackQuery):
    info_text = await tld(cb.message.chat.id, "select_lang")
    button = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇺🇸 English", callback_data=f"lang.en"),
                InlineKeyboardButton("🇧🇷 Português", callback_data=f"lang.pt"),
                InlineKeyboardButton("🇪🇸 Español", callback_data=f"lang.es"),
            ],
            [
                InlineKeyboardButton(await tld(cb.message.chat.id, "BACK_BNT"), callback_data="start_back"),
            ]
        ]
    )
    await client.edit_message_text(
        chat_id=cb.message.chat.id,
        message_id=cb.message.id,
        text=info_text.format(await tld(cb.message.chat.id, "language_flag")),
        reply_markup=button,
    )

@WhiterX.on_callback_query(filters.regex(pattern="^lang\.(.+?)"))
async def infos(c: WhiterX, cb: CallbackQuery):
    try:
        lang = cb.data.split(".")[1]
    except ValueError:
        return print(cb.data)
    await add_lang(cb.message.chat.id, lang)
    time.sleep(0.5)
    info_text = await tld(cb.message.chat.id, "language_switch_success")
    button = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(await tld(cb.message.chat.id, "BACK_BNT"), callback_data="start_back"),
            ]
        ]
    )
    await c.edit_message_text(
        chat_id=cb.message.chat.id,
        message_id=cb.message.id,
        text=info_text.format(await tld(cb.message.chat.id, "language_flag")),
        reply_markup=button,
    )

@WhiterX.on_message(filters.command(["setlang", "lang"]))
@require_admin(ChatPrivileges(can_change_info=True), allow_in_private=True)
async def set_lang(c: WhiterX, m: Message):
    lang = input_str(m).lower()
    if not lang:
        return await m.reply(await tld(m.chat.id, "LANG"))
    if not lang.split()[0] in LANGS:
        return await m.reply(await tld(m.chat.id, "LANG_"))
    await add_lang(m.chat.id, lang.split()[0])
    await asyncio.sleep(0.5)
    await m.reply(await tld(m.chat.id, "LANG_SET"))


@WhiterX.on_callback_query(filters.regex(pattern=r"^help_menu"))
@WhiterX.on_message(filters.command("help") & filters.private)
async def help_menu(c: WhiterX, m: Union[Message, CallbackQuery]):
    reply_msg = m.edit_message_text if isinstance(m, CallbackQuery) else m.reply_text
    msg = m if isinstance(m, Message) else m.message
    buttons: list = []
    for help in sorted(HELPABLE):
        buttons.append(InlineKeyboardButton(await tld(msg.chat.id, f"help-name-{help}"), f"help_plugin {help}"))

    # Divides the button in a 3x3 shape
    keyboard = [buttons[i:i+3] for i in range(0, len(buttons), 3)]

    # Add a back button
    if isinstance(m, CallbackQuery):
        keyboard.append([InlineKeyboardButton(await tld(msg.chat.id, "BACK_BNT"), "start_back")])

    await reply_msg(
        (await tld(msg.chat.id, "HELP_MSG")).format(c.me.first_name),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

@WhiterX.on_callback_query(filters.regex(pattern="^help_plugin (?P<module>.+)"))
async def help_plugin(c: WhiterX, cb: CallbackQuery):
    match = cb.matches[0]["module"]
    keyboard = [InlineKeyboardButton(await tld(cb.message.chat.id, "BACK_BNT"), "help_menu")]
    text = (await tld(cb.message.chat.id, "HELP_BASE")).format(await tld(cb.message.chat.id, f"help-name-{match}")) + await tld(cb.message.chat.id, f"help-plugin-{match}")
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup([keyboard]))