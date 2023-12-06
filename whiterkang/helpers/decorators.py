# WhiterKang Bot
# Copyright (C) 2023 BubbalooTeam
#
# This file is a part of < https://github.com/BubbalooTeam/WhiterRobot/ >
# PLease read the MIT License Agreement in 
# <https://www.github.com/BubbalooTeam/WhiterRobot/blob/main/LICENSE/>.

## WhiterKang Decorators

import logging

from typing import List, Optional, Union

from hydrogram import filters
from hydrogram.types import Message, CallbackQuery, ChatPrivileges
from hydrogram.enums import ChatMemberStatus, ChatType

from functools import partial, wraps


from whiterkang import WhiterX
from whiterkang.helpers import is_disabled, check_perms

DISABLABLE_CMDS: List[str] = []

def input_str(message) -> str:
    return " ".join(message.text.split()[1:])

def disableable_dec(command):
    if command not in DISABLABLE_CMDS:
        logging.info(
            f"Adding {command} to the disableable commands...",
        )
        DISABLABLE_CMDS.append(command)

    def decorator(func):
        async def wrapper(c: WhiterX, message: Message, *args, **kwargs):
            chat_id = message.chat.id

            check = await is_disabled(chat_id, command)
            if check:
                return

            return await func(c, message, *args, **kwargs)

        return wrapper

    return decorator


class InlineHandler:
    """This class is a python interface to InlineHandler"""
    def __init__(self):
        self.INLINE_CMDS = []

    def add_cmd(
        self,
        command: str,
        txt_description: str,
        thumb_url: str,
        aliases: Optional[list] = None,
    ):
        self.INLINE_CMDS.append(
            {
                "command": command,
                "txt_description": txt_description,
                "url_thumb": thumb_url,
                "aliases": aliases or [],
            }
        )

    def search_cmds(self, query: Optional[str] = None):
        return [
            cmd
            for cmd in sorted(self.INLINE_CMDS, key=lambda k: k["command"])
            if (
                not query
                or query in cmd["command"]
                or any(query in alias for alias in cmd["aliases"])
            )
        ]
    

def require_admin(
    permissions: Optional[ChatPrivileges] = None,
    allow_in_private: bool = False,
    complain_missing_perms: bool = True,
):
    """Decorator that checks if the user is an admin in the chat.

    Parameters
    ----------
    permissions: ChatPrivileges
        The permissions to check for.
    allow_in_private: bool
        Whether to allow the command in private chats or not.
    complain_missing_perms: bool
        Whether to complain about missing permissions or not, otherwise the
        function will not be called and the user will not be notified.

    Returns
    -------
    Callable
        The decorated function.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(client: WhiterX, m: Union[CallbackQuery, Message], *args, **kwargs):
            if isinstance(m, CallbackQuery):
                sender = partial(m.answer, show_alert=True)
                msg = m.message
            elif isinstance(m, Message):
                sender = m.reply_text
                msg = m
            else:
                raise NotImplementedError(
                    f"require_admin can't process updates with the type '{m.__name__}' yet."
                )

            # We don't actually check private and channel chats.
            if msg.chat.type == ChatType.PRIVATE:
                if allow_in_private:
                    return await func(client, m, *args, *kwargs)
                return await sender("<i>Isso é apenas para grupos!!</i>")
            if msg.chat.type == ChatType.CHANNEL:
                return await func(client, m, *args, *kwargs)
            has_perms = await check_perms(m, permissions, complain_missing_perms)
            if has_perms:
                return await func(client, m, *args, *kwargs)
            return None

        return wrapper

    return decorator


inline_handler = InlineHandler()
