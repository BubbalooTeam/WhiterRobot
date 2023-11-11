# WhiterKang Bot
# Copyright (C) 2022 KuuhakuTeam
#
# This file is based of < https://github.com/KuuhakuTeam/YuunaRobot/ >
# PLease read the GNU v3.0 License Agreement in 
# <https://www.github.com/KuuhakuTeam/YuunaRobot/blob/master/LICENSE/>.

import os
import time
import logging

from dotenv import load_dotenv
from pyrogram import Client
from pyrogram.enums import ParseMode

from . import version, Config

if os.path.isfile("config.env"):
    load_dotenv("config.env")


START_TIME = time.time()

class WhiterKangBOT(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            name=name,
            app_version=f"WhiterRobot {version.__WhiterX_version__}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            parse_mode=ParseMode.HTML,
            workers=24,
            in_memory=True,
            plugins={"root": "whiterkang/plugins"},
            sleep_threshold=180,
        )

    async def start(self):
        await super().start()
        self.me = await self.get_me()
        text_ = f"#WhiterKang #Logs\n\n<i>WhiterKang is now working.</i>\n\n<b>Version</b> : <code>{version.__WhiterX_version__}</code>\n<b>System</b> : <code>{self.system_version}</code>"
        await self.send_message(chat_id=Config.GP_LOGS, text=text_)
        logging.info("WhiterKang is playing now '-'...")

    async def stop(self):
        text_ = "#WhiterKang #Logs\n\n<i>WhiterKang will change batteries.</i>"
        await self.send_message(chat_id=Config.GP_LOGS, text=text_)
        await super().stop()
        logging.info("WhiterKang will change batteries ...")

    async def send_log(self, text: str, *args, **kwargs):
        await self.send_message(
            chat_id=Config.GP_LOGS,
            text=text,
            *args,
            **kwargs,
        )

    async def send_err(self, e: str):
        await self.send_message(
            chat_id=Config.GP_LOGS,
            text="#WhiterKang #ERROR #LOGS\n\n{}".format(e)
        )


WhiterX = WhiterKangBOT()
